import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger("database")

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017"
DATABASE_NAME = "ransomguard"

# Global client reference
client: AsyncIOMotorClient = None
database: AsyncIOMotorDatabase = None


async def connect_to_mongo():
    """
    Establish connection to MongoDB using Motor async client.
    """
    global client, database

    try:
        client = AsyncIOMotorClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000,
        )

        # Verify connection
        await client.admin.command("ping")

        database = client[DATABASE_NAME]

        # Create collections and indexes
        await create_indexes()

        logger.info(f"Connected to MongoDB at {MONGO_URI}")
        logger.info(f"Using database: {DATABASE_NAME}")

    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """
    Close the MongoDB connection gracefully.
    """
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed")


async def create_indexes():
    """
    Create necessary indexes for all collections.
    """
    global database

    # threat_logs indexes
    await database["threat_logs"].create_index("timestamp")
    await database["threat_logs"].create_index("threat_level")
    await database["threat_logs"].create_index("file_path")
    await database["threat_logs"].create_index("status")

    # system_logs indexes
    await database["system_logs"].create_index("timestamp")
    await database["system_logs"].create_index("event_type")

    # reports indexes
    await database["reports"].create_index("created_at")
    await database["reports"].create_index("report_type")

    # settings indexes
    await database["settings"].create_index("key", unique=True)

    logger.info("MongoDB indexes created successfully")


def get_database() -> AsyncIOMotorDatabase:
    """
    Return the active database instance.
    """
    global database
    if database is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return database


def get_collection(collection_name: str):
    """
    Return a specific collection from the database.
    """
    db = get_database()
    return db[collection_name]