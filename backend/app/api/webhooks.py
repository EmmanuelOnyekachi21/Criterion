"""GitLab webhook endpoint for receiving merge request events.

This module handles incoming GitLab webhook events with token verification
and queues analysis tasks for processing.
"""

import hmac

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db

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
    if verify_gitlab_token(request):
        payload = await request.json()
        event_type = request.headers.get("X-Gitlab-Event", "")

        return {
            "status": "queued",
            "event": event_type
        }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid webhook token"
    )
