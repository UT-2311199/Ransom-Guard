from typing import Dict, Any
import psutil
from utils.logger import setup_logger

logger = setup_logger("process_service", "logs/app.log")


class ProcessService:
    """Service for process management operations."""

    def terminate(self, pid: int, force: bool = False) -> Dict[str, Any]:
        """
        Terminate a process by PID.

        Args:
            pid: Process ID
            force: Force kill

        Returns:
            Result dictionary
        """
        from datetime import datetime

        try:
            proc = psutil.Process(pid)
            proc_name = proc.name()
            proc_exe = None
            try:
                proc_exe = proc.exe()
            except (psutil.AccessDenied, OSError):
                pass

            if force:
                proc.kill()
                action = "killed"
            else:
                proc.terminate()
                action = "terminated"

            logger.warning(f"Process {proc_name} (PID: {pid}) {action}")

            return {
                "success": True,
                "pid": pid,
                "process_name": proc_name,
                "executable": proc_exe,
                "action": action,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except psutil.NoSuchProcess:
            return {
                "success": False,
                "pid": pid,
                "error": f"Process with PID {pid} does not exist",
                "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            }
        except psutil.AccessDenied:
            return {
                "success": False,
                "pid": pid,
                "error": f"Access denied: insufficient permissions to terminate PID {pid}",
                "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Unexpected error terminating process {pid}: {e}")
            return {
                "success": False,
                "pid": pid,
                "error": str(e),
                "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            }