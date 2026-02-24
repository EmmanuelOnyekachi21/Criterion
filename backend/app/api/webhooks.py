"""GitLab webhook endpoint for receiving merge request events.

This module handles incoming GitLab webhook events with token verification
and queues analysis tasks for processing.
"""

import hmac

from fastapi import APIRouter, Depends, HTTPException, Request, status

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert

from app.config import settings

from app.database import get_db

from app.models.webhooks import Webhooks
from app.models.merge_request import MergeRequests
from app.models.analysis import Analyses

from app.schema.webhooks import GitLabWebhookPayload

from app.tasks.analysis import analyze_merge_request

router = APIRouter()


def verify_gitlab_token(request: Request) -> bool:
    """Verify the GitLab webhook token from request headers.

    Args:
        request (Request): The incoming HTTP request.

    Returns:
        bool: True if token is valid, False otherwise.
    """
    gitlab_token = request.headers.get('X-Gitlab-Token', None)
    if not gitlab_token:
        return False
    return hmac.compare_digest(gitlab_token, settings.gitlab_webhook_secret)


@router.post('gitlab/', status_code=202)
async def receive_webhook(
    payload: GitLabWebhookPayload,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Receive and process GitLab webhook events.

    Verifies the webhook token and queues the event for processing.
    Returns 202 Accepted if the token is valid.

    Args:
        request (Request): The incoming HTTP request containing webhook data.
        db (AsyncSession): Database session from dependency injection.

    Returns:
        dict: Status object with queued event information.

    Raises:
        HTTPException: 401 if webhook token is invalid.
    """
    if not verify_gitlab_token(request):
        raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid webhook token"
    )

    unique_key = request.headers.get("X-Gitlab-Event-UUID", "")

    if not unique_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No unique key provided"
        )
    
    # Checking webhooks table if incoming webhook already exist.
    stmt = select(Webhooks).filter(Webhooks.gitlab_event_uuid == unique_key)
    obj = await db.execute(stmt)
    obj = obj.scalar_one_or_none()

    if obj:
        return {
            "status": "Already exists",
            "event": unique_key
        }
    action = payload.object_attributes.action

    if action in ["open", "update"]:
        stmt = insert(MergeRequests).values(
            gitlab_project_id=payload.project.id,
            gitlab_mr_iid=payload.object_attributes.iid,
            gitlab_mr_id=payload.object_attributes.id,
            project_name=payload.project.name,
            project_namespace=payload.project.namespace,
            title=payload.object_attributes.title,
            author_username=payload.user.username,
            source_branch=payload.object_attributes.source_branch,
            target_branch=payload.object_attributes.target_branch,
            mr_url=payload.object_attributes.url,
            state=payload.object_attributes.state,
            gitlab_created_at=payload.object_attributes.created_at,
            first_seen_at=func.now(),               # Only set on INSERT
            last_updated_at=func.now(),
        )
        
        # Handle conflicts: if (gitlab_project_id, gitlab_mr_iid) already exists
        stmt = stmt.on_conflict_do_update(
            index_elements=['gitlab_project_id', 'gitlab_mr_iid'],
            set_={
                "title": stmt.excluded.title,
                "state": stmt.excluded.state,
                "source_branch": stmt.excluded.source_branch,
                "target_branch": stmt.excluded.target_branch,
                "mr_url": stmt.excluded.mr_url,
                "last_updated_at": func.now(),
            }
        ).returning(MergeRequests.id)

        mr = await db.execute(stmt)
        mr_id = mr.scalar_one()

        # Create Analysis method with status pending.
        stmt = insert(Analyses).values(
            mr_id=mr_id,
            trigger_type="webhook",
            status="pending"
        ).returning(Analyses.id)

        analysis = await db.execute(stmt)
        analysis_id = analysis.scalar_one()

        # Insert into the webhooks table
        stmt = insert(Webhooks).values(
            gitlab_event_uuid=unique_key,
            event_type=payload.event_type,
            payload=payload.model_dump(),
            # status is received by default so no need to declare
            analysis_id=analysis_id
        )

        await db.execute(stmt)

        # Enqueue celery task with (gitlab_project_id, gitlab_mr_iid, analysis_id)
        task = analyze_merge_request.delay(payload.project.id, payload.object_attributes.iid, analysis_id)


        return {
            "status": "queued",
            "event_type": payload.object_kind
        }
