"""
System monitoring API endpoints.
Provides endpoints for retrieving system resource information and health status.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from ...services.system_monitor import system_monitor
from ...middleware.auth import get_current_user
from ...models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/resources", response_model=Dict[str, Any])
async def get_system_resources(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get comprehensive system resource information.
    
    Returns:
        Dict containing CPU, memory, disk, network, database, and queue statistics
    """
    try:
        resources = await system_monitor.get_system_resources()
        return {
            "success": True,
            "data": resources
        }
    except Exception as e:
        logger.error(f"Error retrieving system resources: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve system resources"
        )


@router.get("/health", response_model=Dict[str, Any])
async def get_system_health(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get system health status based on resource usage.
    
    Returns:
        Dict containing health status and key metrics
    """
    try:
        resources = await system_monitor.get_system_resources()
        health_status = system_monitor.get_system_health_status(resources)
        
        return {
            "success": True,
            "data": {
                "status": health_status,
                "timestamp": resources["timestamp"],
                "summary": {
                    "cpu_percent": resources["cpu"]["percent"],
                    "memory_percent": resources["memory"]["percent"],
                    "disk_percent": resources["disk"]["percent"],
                    "database_connections": resources["database"]["connections"],
                    "queue_pending": resources["queue"]["pending"]
                }
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving system health: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve system health status"
        )


@router.get("/cpu", response_model=Dict[str, Any])
async def get_cpu_usage(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current CPU usage information."""
    try:
        cpu_percent = system_monitor.get_cpu_usage()
        return {
            "success": True,
            "data": {
                "percent": cpu_percent,
                "count": system_monitor.get_system_resources()["cpu"]["count"],
                "timestamp": system_monitor.get_system_resources()["timestamp"]
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving CPU usage: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve CPU usage"
        )


@router.get("/memory", response_model=Dict[str, Any])
async def get_memory_usage(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current memory usage information."""
    try:
        memory_info = system_monitor.get_memory_usage()
        return {
            "success": True,
            "data": {
                **memory_info,
                "used_formatted": system_monitor.format_bytes(memory_info["used"]),
                "total_formatted": system_monitor.format_bytes(memory_info["total"]),
                "available_formatted": system_monitor.format_bytes(memory_info["available"])
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving memory usage: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve memory usage"
        )


@router.get("/disk", response_model=Dict[str, Any])
async def get_disk_usage(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get current disk usage information."""
    try:
        disk_info = system_monitor.get_disk_usage()
        return {
            "success": True,
            "data": {
                **disk_info,
                "used_formatted": system_monitor.format_bytes(disk_info["used"]),
                "total_formatted": system_monitor.format_bytes(disk_info["total"]),
                "free_formatted": system_monitor.format_bytes(disk_info["free"])
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving disk usage: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve disk usage"
        )