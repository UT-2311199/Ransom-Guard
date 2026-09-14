import asyncio
import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routes import (
    analytics,
    monitor,
    ml_status,
    prediction,
    reports,
    settings,
    system,
    threats,
)
from database.connection import connect_to_mongo, close_mongo_connection
from monitor.file_monitor import FileSystemMonitor
from monitor.process_monitor import ProcessMonitor
from utils.logger import setup_logger

logger = setup_logger("main", "logs/main.log")

# Global monitor instances
file_monitor_instance: FileSystemMonitor = None
process_monitor_instance: ProcessMonitor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan - startup and shutdown events.
    """
    global file_monitor_instance, process_monitor_instance

    logger.info("=== RansomGuard Backend Starting ===")

    # Connect to MongoDB
    await connect_to_mongo()
    logger.info("MongoDB connection established")

    # Create required directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    logger.info("Required directories created")

    # Start file system monitor
    try:
        file_monitor_instance = FileSystemMonitor(watch_path="/")
        file_monitor_instance.start()
        logger.info("File system monitor started")
    except Exception as e:
        logger.error(f"Failed to start file system monitor: {e}")

    # Start process monitor
    try:
        process_monitor_instance = ProcessMonitor()
        asyncio.create_task(process_monitor_instance.start_monitoring())
        logger.info("Process monitor started")
    except Exception as e:
        logger.error(f"Failed to start process monitor: {e}")

    # Store monitors in app state
    app.state.file_monitor = file_monitor_instance
    app.state.process_monitor = process_monitor_instance

    logger.info("=== RansomGuard Backend Ready ===")

    yield

    # Shutdown
    logger.info("=== RansomGuard Backend Shutting Down ===")

    if file_monitor_instance:
        file_monitor_instance.stop()
        logger.info("File system monitor stopped")

    if process_monitor_instance:
        process_monitor_instance.stop()
        logger.info("Process monitor stopped")

    await close_mongo_connection()
    logger.info("MongoDB connection closed")
    logger.info("=== RansomGuard Backend Stopped ===")


# Initialize FastAPI application
app = FastAPI(
    title="RansomGuard API",
    description="Machine Learning Based Ransomware Detection Using File System Behavior Analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc} | Path: {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error": str(exc),
            "path": str(request.url.path),
        },
    )


# Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    return {
        "success": True,
        "message": "RansomGuard API is running",
        "version": "1.0.0",
        "status": "healthy",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "success": True,
        "status": "healthy",
        "service": "RansomGuard",
        "version": "1.0.0",
    }


# Register all routers
app.include_router(system.router, prefix="/api/v1", tags=["System"])
app.include_router(monitor.router, prefix="/api/v1", tags=["Monitor"])
app.include_router(prediction.router, prefix="/api/v1", tags=["Prediction"])
app.include_router(threats.router, prefix="/api/v1", tags=["Threats"])
app.include_router(analytics.router, prefix="/api/v1", tags=["Analytics"])
app.include_router(reports.router, prefix="/api/v1", tags=["Reports"])
app.include_router(settings.router, prefix="/api/v1", tags=["Settings"])
app.include_router(ml_status.router, prefix="/api/v1", tags=["ML"])

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        workers=1,
    )