"""
System monitoring service for COT Studio platform.
Provides real-time system resource monitoring including CPU, memory, disk usage,
database connections, and task queue status.
"""

import psutil
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy import text
from ..core.database import get_db
from ..core.config import settings
import logging
import subprocess
import json

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
    
    @staticmethod
    def get_gpu_info() -> Dict[str, Any]:
        """Get GPU information using nvidia-smi."""
        try:
            # Try to get GPU info from nvidia-smi
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=index,name,driver_version,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu', 
                 '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return {"available": False, "error": "NVIDIA GPU not found"}
            
            gpus = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 8:
                        gpus.append({
                            "index": int(parts[0]),
                            "name": parts[1],
                            "driver_version": parts[2],
                            "memory_total_mb": float(parts[3]),
                            "memory_used_mb": float(parts[4]),
                            "memory_free_mb": float(parts[5]),
                            "utilization_percent": float(parts[6]),
                            "temperature_c": float(parts[7])
                        })
            
            # Get CUDA version from nvidia-smi
            cuda_version = "N/A"
            try:
                cuda_result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=compute_cap', '--format=csv,noheader'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                # Get driver-supported CUDA version
                version_result = subprocess.run(
                    ['nvidia-smi'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if version_result.returncode == 0:
                    # Parse CUDA version from nvidia-smi output header
                    for line in version_result.stdout.split('\n'):
                        if 'CUDA Version' in line:
                            # Extract CUDA Version: 13.0
                            parts = line.split('CUDA Version:')
                            if len(parts) > 1:
                                cuda_version = parts[1].strip().split()[0]
                                break
            except Exception as e:
                logger.debug(f"Could not get CUDA version: {e}")
            
            # Try to get cuDNN version
            cudnn_version = "N/A"
            try:
                # Try to import torch and get cuDNN version
                import torch
                if torch.cuda.is_available():
                    cudnn_version = f"{torch.backends.cudnn.version()}"
            except Exception as e:
                logger.debug(f"Could not get cuDNN version: {e}")
            
            # Calculate total memory
            total_memory_gb = sum(gpu["memory_total_mb"] for gpu in gpus) / 1024
            used_memory_gb = sum(gpu["memory_used_mb"] for gpu in gpus) / 1024
            
            return {
                "available": True,
                "count": len(gpus),
                "gpus": gpus,
                "cuda_version": cuda_version,
                "cudnn_version": cudnn_version,
                "total_memory_gb": round(total_memory_gb, 2),
                "used_memory_gb": round(used_memory_gb, 2),
                "memory_percent": round((used_memory_gb / total_memory_gb * 100) if total_memory_gb > 0 else 0, 2)
            }
            
        except FileNotFoundError:
            return {"available": False, "error": "nvidia-smi not found"}
        except subprocess.TimeoutExpired:
            return {"available": False, "error": "nvidia-smi timeout"}
        except Exception as e:
            logger.error(f"Error getting GPU info: {e}")
            return {"available": False, "error": str(e)}
    
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
            gpu_info = cls.get_gpu_info()
            
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
                "gpu": gpu_info,
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
                "gpu": {"available": False},
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