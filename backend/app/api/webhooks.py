"""GitLab webhook endpoint for receiving merge request events.

This module handles incoming GitLab webhook events with token verification
and queues analysis tasks for processing.
"""

import hmac
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.logger import logger
from app.models.analysis import Analyses
from app.models.merge_request import MergeRequests
from app.models.webhooks import Webhooks
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


@router.post('/gitlab/', status_code=202)
async def receive_webhook(
    payload: GitLabWebhookPayload,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Receive and process GitLab webhook events.

    Verifies the webhook token, stores the event, and queues analysis tasks
    for merge request open/update actions.

    Args:
        payload (GitLabWebhookPayload): Validated webhook payload.
        request (Request): The incoming HTTP request.
        db (AsyncSession): Database session from dependency injection.

    Returns:
        dict: Status object with queued event information.

    Raises:
        HTTPException: 401 if webhook token is invalid.
        HTTPException: 400 if webhook is missing required headers.
    """
    # Log incoming webhook
    logger.info(
        f"Webhook received: event_type={payload.event_type}, "
        f"project={payload.project.name}, "
        f"mr_iid={payload.object_attributes.iid}"
    )

    if not verify_gitlab_token(request):
        logger.warning(
            f"Invalid webhook token from IP: {request.client.host}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook token"
        )

    unique_key = request.headers.get("X-Gitlab-Event-UUID", "")

    if not unique_key:
        logger.error("Webhook missing X-Gitlab-Event-UUID header")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No unique key provided"
        )

    # Check if webhook already exists
    stmt = select(Webhooks).filter(Webhooks.gitlab_event_uuid == unique_key)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        logger.info(f"Duplicate webhook ignored: {unique_key}")
        return {
            "status": "already_processed",
            "event": unique_key
        }

    action = payload.object_attributes.action

    if action in ["open", "update"]:
        # Process webhook
        logger.info(f"Processing webhook {unique_key}: action={action}")

        # Parse gitlab_created_at from ISO string to datetime
        gitlab_created_at = None
        if payload.object_attributes.created_at:
            try:
                gitlab_created_at = datetime.fromisoformat(
                    payload.object_attributes.created_at.replace('Z', '+00:00')
                )
            except (ValueError, AttributeError) as e:
                logger.warning(f"Failed to parse created_at: {e}")

        # Upsert merge request
        stmt = insert(MergeRequests).values(
            gitlab_project_id=payload.project.id,
            gitlab_mr_iid=payload.object_attributes.iid,
            gitlab_mr_id=payload.object_attributes.id,
            project_name=payload.project.name,
            project_namespace=payload.project.path_with_namespace,
            title=payload.object_attributes.title,
            author_username=payload.user.username,
            source_branch=payload.object_attributes.source_branch,
            target_branch=payload.object_attributes.target_branch,
            mr_url=payload.object_attributes.url,
            state=payload.object_attributes.state,
            gitlab_created_at=gitlab_created_at,
            first_seen_at=func.now(),
            last_updated_at=func.now(),
        )

        # Handle conflicts: update if exists
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

        # Create analysis record with pending status
        stmt = insert(Analyses).values(
            mr_id=mr_id,
            trigger_type="webhook",
            status="pending"
        ).returning(Analyses.id)

        analysis = await db.execute(stmt)
        analysis_id = analysis.scalar_one()

        # Insert webhook record
        stmt = insert(Webhooks).values(
            gitlab_event_uuid=unique_key,
            event_type=payload.event_type or payload.object_kind,
            payload=payload.model_dump(),
            status="received",
            analysis_id=analysis_id
        )

        await db.execute(stmt)
        await db.commit()

        # Enqueue Celery task
        task = analyze_merge_request.delay(
            payload.project.id,
            payload.object_attributes.iid,
            analysis_id
        )

        logger.info(
            f"Analysis queued: task_id={task.id}, "
            f"analysis_id={analysis_id}"
        )

        return {
            "status": "queued",
            "event_type": payload.object_kind,
            "analysis_id": analysis_id,
        }
    else:
        # Log ignored actions
        logger.info(
            f"Webhook action '{action}' ignored for MR "
            f"{payload.object_attributes.iid}"
        )
        return {
            "status": "ignored",
            "event_type": payload.object_kind,
            "action": action
        }
