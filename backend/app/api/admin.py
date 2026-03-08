"""Admin endpoints for database inspection (development only)."""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.analysis import Analyses
from app.models.merge_request import MergeRequests

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/merge-requests", response_model=List[Dict[str, Any]])
async def list_merge_requests(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """List recent merge requests from database.

    Args:
        limit (int): Maximum number of MRs to return (default 10).
        db (AsyncSession): Database session from dependency injection.

    Returns:
        List[Dict[str, Any]]: List of merge request summaries.
    """
    result = await db.execute(
        select(MergeRequests)
        .order_by(MergeRequests.gitlab_created_at.desc())
        .limit(limit)
    )
    mrs = result.scalars().all()
    return [
        {
            "id": mr.id,
            "mr_iid": mr.gitlab_mr_iid,
            "gitlab_project_id": mr.gitlab_project_id,
            "title": mr.title,
            "state": mr.state,
            "source_branch": mr.source_branch,
            "target_branch": mr.target_branch,
            "author": mr.author_username,
            "created_at": (
                mr.gitlab_created_at.isoformat()
                if mr.gitlab_created_at else None
            ),
            "updated_at": (
                mr.last_updated_at.isoformat()
                if mr.last_updated_at else None
            ),
        }
        for mr in mrs
    ]


@router.get("/merge-requests/{mr_id}", response_model=Dict[str, Any])
async def get_merge_request(
    mr_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific merge request by ID.

    Args:
        mr_id (int): Database ID of the merge request.
        db (AsyncSession): Database session from dependency injection.

    Returns:
        Dict[str, Any]: Merge request details, or empty dict if not found.

    Raises:
        HTTPException: 404 if merge request not found.
    """
    result = await db.execute(
        select(MergeRequests).where(MergeRequests.id == mr_id)
    )
    mr = result.scalar_one_or_none()
    if not mr:
        raise HTTPException(status_code=404, detail="Merge request not found")

    return {
        "id": mr.id,
        "gitlab_mr_iid": mr.gitlab_mr_iid,
        "gitlab_project_id": mr.gitlab_project_id,
        "title": mr.title,
        "state": mr.state,
        "source_branch": mr.source_branch,
        "target_branch": mr.target_branch,
        "author": mr.author_username,
        "mr_url": mr.mr_url,
        "created_at": (
            mr.gitlab_created_at.isoformat()
            if mr.gitlab_created_at else None
        ),
        "updated_at": (
            mr.last_updated_at.isoformat()
            if mr.last_updated_at else None
        ),
    }


@router.get('/analyses', response_model=List[Dict[str, Any]])
async def get_analyses(db: AsyncSession = Depends(get_db)):
    """Get all analyses ordered by creation date.

    Args:
        db (AsyncSession): Database session from dependency injection.

    Returns:
        List[Dict[str, Any]]: List of analysis records.
    """
    stmt = select(Analyses).order_by(Analyses.created_at.desc())
    result = await db.execute(stmt)
    analyses = result.scalars().all()

    return [
        {
            'id': analysis.id,
            'merge_request_id': analysis.mr_id,
            'confidence_score': analysis.confidence_score,
            'status': analysis.status,
            'action_taken': analysis.action_taken,
            'error_message': analysis.error_message,
            'created_at': (
                analysis.created_at.isoformat()
                if analysis.created_at else None
            ),
            'started_at': (
                analysis.started_at.isoformat()
                if analysis.started_at else None
            ),
            'acceptance_criteria': analysis.acceptance_criteria,
        }
        for analysis in analyses
    ]
