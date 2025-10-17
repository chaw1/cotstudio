"""
Analytics API endpoints for user contributions and system statistics.
Provides data for dashboard visualizations and reporting.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from ...core.database import get_db
from ...middleware.auth import get_current_user
from ...models.user import User
from ...models.project import Project
from ...models.file import File
from ...models.cot import COTItem
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/user-contributions", response_model=Dict[str, Any])
async def get_user_contributions(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get user contribution data for visualization.
    
    Returns user-dataset relationships with node sizes based on data volume.
    """
    try:
        # Get users with their project counts
        users_query = (
            db.query(
                User.id,
                User.username,
                User.email,
                func.count(Project.id).label('project_count')
            )
            .outerjoin(Project, User.id == Project.owner_id)
            .group_by(User.id, User.username, User.email)
            .order_by(desc('project_count'))
            .limit(limit)
        )
        
        users_data = users_query.all()
        
        # Get COT item counts for each user separately to avoid transaction issues
        user_cot_counts = {}
        for user in users_data:
            cot_count = (
                db.query(func.count(COTItem.id))
                .join(Project, COTItem.project_id == Project.id)
                .filter(Project.owner_id == user.id)
                .scalar() or 0
            )
            user_cot_counts[user.id] = cot_count
        
        # Get projects with their statistics
        projects_query = (
            db.query(
                Project.id,
                Project.name,
                Project.owner_id,
                func.count(File.id).label('file_count'),
                func.coalesce(func.count(COTItem.id), 0).label('cot_count')
            )
            .outerjoin(File, Project.id == File.project_id)
            .outerjoin(COTItem, Project.id == COTItem.project_id)
            .group_by(Project.id, Project.name, Project.owner_id)
            .order_by(desc('cot_count'))
            .limit(limit * 2)  # Get more projects to ensure good visualization
        )
        
        projects_data = projects_query.all()
        
        # Format data for visualization
        users = []
        for user in users_data:
            total_cot_items = user_cot_counts.get(user.id, 0)
            users.append({
                'id': f"user_{user.id}",
                'name': user.username,
                'email': user.email,
                'type': 'user',
                'project_count': user.project_count,
                'total_cot_items': total_cot_items,
                # Node size based on total COT items created
                'size': max(20, min(80, 20 + (total_cot_items * 2)))
            })
        
        datasets = []
        relationships = []
        
        for project in projects_data:
            dataset_id = f"project_{project.id}"
            datasets.append({
                'id': dataset_id,
                'name': project.name,
                'type': 'project',
                'file_count': project.file_count,
                'cot_count': project.cot_count,
                'owner_id': project.owner_id,
                # Node size based on COT count
                'size': max(15, min(60, 15 + (project.cot_count * 1.5)))
            })
            
            # Create relationship between user and project
            if project.owner_id:
                relationships.append({
                    'source': f"user_{project.owner_id}",
                    'target': dataset_id,
                    'type': 'owns'
                })
        
        return {
            "success": True,
            "data": {
                "users": users,
                "datasets": datasets,
                "relationships": relationships,
                "summary": {
                    "total_users": len(users),
                    "total_projects": len(datasets),
                    "total_relationships": len(relationships),
                    "total_cot_items": sum(user_cot_counts.values())
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting user contributions: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user contribution data"
        )


@router.get("/dashboard-stats", response_model=Dict[str, Any])
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get comprehensive dashboard statistics.
    """
    try:
        # Get basic counts
        total_users = db.query(func.count(User.id)).scalar() or 0
        total_projects = db.query(func.count(Project.id)).scalar() or 0
        total_files = db.query(func.count(File.id)).scalar() or 0
        total_cot_items = db.query(func.count(COTItem.id)).scalar() or 0
        
        # Get recent activity (projects created in last 30 days)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        recent_projects = (
            db.query(func.count(Project.id))
            .filter(Project.created_at >= thirty_days_ago)
            .scalar() or 0
        )
        
        recent_cot_items = (
            db.query(func.count(COTItem.id))
            .filter(COTItem.created_at >= thirty_days_ago)
            .scalar() or 0
        )
        
        # Get top contributors
        top_contributors = (
            db.query(
                User.username,
                func.count(Project.id).label('project_count')
            )
            .outerjoin(Project, User.id == Project.owner_id)
            .group_by(User.id, User.username)
            .order_by(desc('project_count'))
            .limit(5)
            .all()
        )
        
        # Get COT counts for top contributors separately
        top_contributors_with_cot = []
        for contrib in top_contributors:
            user_id = (
                db.query(User.id)
                .filter(User.username == contrib.username)
                .scalar()
            )
            cot_count = (
                db.query(func.count(COTItem.id))
                .join(Project, COTItem.project_id == Project.id)
                .filter(Project.owner_id == user_id)
                .scalar() or 0
            )
            top_contributors_with_cot.append({
                'username': contrib.username,
                'project_count': contrib.project_count,
                'cot_count': cot_count
            })
        
        # Get project status distribution
        project_status_dist = (
            db.query(
                Project.status,
                func.count(Project.id).label('count')
            )
            .group_by(Project.status)
            .all()
        )
        
        return {
            "success": True,
            "data": {
                "totals": {
                    "users": total_users,
                    "projects": total_projects,
                    "files": total_files,
                    "cot_items": total_cot_items
                },
                "recent_activity": {
                    "projects_30d": recent_projects,
                    "cot_items_30d": recent_cot_items
                },
                "top_contributors": top_contributors_with_cot,
                "project_status_distribution": [
                    {
                        "status": status.status,
                        "count": status.count
                    }
                    for status in project_status_dist
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve dashboard statistics"
        )


@router.get("/activity-timeline", response_model=Dict[str, Any])
async def get_activity_timeline(
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get activity timeline data for the specified number of days.
    """
    try:
        from datetime import datetime, timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get daily project creation counts
        project_timeline = (
            db.query(
                func.date(Project.created_at).label('date'),
                func.count(Project.id).label('count')
            )
            .filter(Project.created_at >= start_date)
            .group_by(func.date(Project.created_at))
            .order_by('date')
            .all()
        )
        
        # Get daily COT item creation counts
        cot_timeline = (
            db.query(
                func.date(COTItem.created_at).label('date'),
                func.count(COTItem.id).label('count')
            )
            .filter(COTItem.created_at >= start_date)
            .group_by(func.date(COTItem.created_at))
            .order_by('date')
            .all()
        )
        
        return {
            "success": True,
            "data": {
                "projects": [
                    {
                        "date": item.date.isoformat(),
                        "count": item.count
                    }
                    for item in project_timeline
                ],
                "cot_items": [
                    {
                        "date": item.date.isoformat(),
                        "count": item.count
                    }
                    for item in cot_timeline
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting activity timeline: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve activity timeline"
        )