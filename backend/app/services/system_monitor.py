"""
System monitoring service for COT Studio platform.
Provides real-time system resource monitoring including CPU, memory, disk usage,
database connections, and task queue status.
"""

import psutil
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy import text
from ..core.database import get_db
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)


class SystemMonitorService:
    """Service for monitoring system resources and performance metrics."""
    
    @staticmethod
    def get_cpu_usage() -> float:
        """Get current CPU usage percentage."""
        try:
            return psutil.cpu_percent(interval=1)
        except Exception as e:
            logger.error(f"Error getting CPU usage: {e}")
            return 0.0
    
    @staticmethod
    def get_memory_usage() -> Dict[str, Any]:
        """Get current memory usage information."""
        try:
            memory = psutil.virtual_memory()
            return {
                "used": memory.used,
                "total": memory.total,
                "percent": memory.percent,
                "available": memory.available
            }
        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
            return {
                "used": 0,
                "total": 0,
                "percent": 0.0,
                "available": 0
            }
    
    @staticmethod
    def get_disk_usage(path: str = "/") -> Dict[str, Any]:
        """Get disk usage information for specified path."""
        try:
            disk = psutil.disk_usage(path)
            return {
                "used": disk.used,
                "total": disk.total,
                "percent": (disk.used / disk.total) * 100,
                "free": disk.free
            }
        except Exception as e:
            logger.error(f"Error getting disk usage: {e}")
            return {
                "used": 0,
                "total": 0,
                "percent": 0.0,
                "free": 0
            }
    
    @staticmethod
    async def get_database_connections() -> int:
        """Get current number of active database connections."""
        try:
            from app.core.database import SessionLocal
            db = SessionLocal()
            try:
                # For PostgreSQL, get active connections count
                result = db.execute(text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"))
                count = result.scalar()
                return count if count else 0
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error getting database connections: {e}")
            return 0
    
    @staticmethod
    def get_process_info() -> Dict[str, Any]:
        """Get current process information."""
        try:
            process = psutil.Process()
            return {
                "pid": process.pid,
                "memory_percent": process.memory_percent(),
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
                "create_time": process.create_time()
            }
        except Exception as e:
            logger.error(f"Error getting process info: {e}")
            return {
                "pid": 0,
                "memory_percent": 0.0,
                "cpu_percent": 0.0,
                "num_threads": 0,
                "create_time": 0
            }
    
    @staticmethod
    def get_network_usage() -> Dict[str, Any]:
        """Get network I/O statistics."""
        try:
            net_io = psutil.net_io_counters()
            return {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv
            }
        except Exception as e:
            logger.error(f"Error getting network usage: {e}")
            return {
                "bytes_sent": 0,
                "bytes_recv": 0,
                "packets_sent": 0,
                "packets_recv": 0
            }
    
    @staticmethod
    async def get_queue_status() -> Dict[str, int]:
        """Get task queue status (placeholder for Celery integration)."""
        try:
            # This would integrate with Celery to get actual queue stats
            # For now, return placeholder values
            return {
                "pending": 0,
                "active": 0,
                "failed": 0,
                "completed": 0
            }
        except Exception as e:
            logger.error(f"Error getting queue status: {e}")
            return {
                "pending": 0,
                "active": 0,
                "failed": 0,
                "completed": 0
            }
    
    @classmethod
    async def get_system_resources(cls) -> Dict[str, Any]:
        """Get comprehensive system resource information."""
        try:
            # Get all system metrics
            cpu_percent = cls.get_cpu_usage()
            memory_info = cls.get_memory_usage()
            disk_info = cls.get_disk_usage()
            process_info = cls.get_process_info()
            network_info = cls.get_network_usage()
            db_connections = await cls.get_database_connections()
            queue_status = await cls.get_queue_status()
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count(),
                    "count_logical": psutil.cpu_count(logical=True)
                },
                "memory": memory_info,
                "disk": disk_info,
                "process": process_info,
                "network": network_info,
                "database": {
                    "connections": db_connections
                },
                "queue": queue_status,
                "system": {
                    "boot_time": psutil.boot_time(),
                    "uptime": datetime.utcnow().timestamp() - psutil.boot_time()
                }
            }
        except Exception as e:
            logger.error(f"Error getting system resources: {e}")
            # Return default values in case of error
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": {"percent": 0.0, "count": 1, "count_logical": 1},
                "memory": {"used": 0, "total": 0, "percent": 0.0, "available": 0},
                "disk": {"used": 0, "total": 0, "percent": 0.0, "free": 0},
                "process": {"pid": 0, "memory_percent": 0.0, "cpu_percent": 0.0, "num_threads": 0, "create_time": 0},
                "network": {"bytes_sent": 0, "bytes_recv": 0, "packets_sent": 0, "packets_recv": 0},
                "database": {"connections": 0},
                "queue": {"pending": 0, "active": 0, "failed": 0, "completed": 0},
                "system": {"boot_time": 0, "uptime": 0}
            }
    
    @classmethod
    def format_bytes(cls, bytes_value: int) -> str:
        """Format bytes to human readable format."""
        bytes_float = float(bytes_value)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_float < 1024.0:
                return f"{bytes_float:.2f} {unit}"
            bytes_float /= 1024.0
        return f"{bytes_float:.2f} PB"
    
    @classmethod
    def get_system_health_status(cls, resources: Dict[str, Any]) -> str:
        """Determine overall system health status based on resource usage."""
        try:
            cpu_percent = resources.get("cpu", {}).get("percent", 0)
            memory_percent = resources.get("memory", {}).get("percent", 0)
            disk_percent = resources.get("disk", {}).get("percent", 0)
            
            # Define thresholds
            if cpu_percent > 90 or memory_percent > 90 or disk_percent > 90:
                return "critical"
            elif cpu_percent > 70 or memory_percent > 70 or disk_percent > 80:
                return "warning"
            elif cpu_percent > 50 or memory_percent > 50 or disk_percent > 60:
                return "moderate"
            else:
                return "healthy"
        except Exception as e:
            logger.error(f"Error determining system health: {e}")
            return "unknown"


# Create a singleton instance
system_monitor = SystemMonitorService()