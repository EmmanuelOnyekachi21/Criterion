"""Webhook model for tracking incoming GitLab webhook events.

This module defines the Webhooks table which stores received webhook events
from GitLab for audit and processing tracking.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Webhooks(Base):
    """GitLab webhook event tracking and storage.

    Stores incoming webhook events from GitLab with their payloads and
    processing status for audit and debugging purposes.

    Attributes:
        id (int): Primary key.
        gitlab_event_uuid (str): Unique event ID from GitLab.
        event_type (str): Type of webhook event (merge_request, etc).
        payload (dict): Full JSON payload from GitLab.
        status (str): Processing status (received/processing/completed).
        received_at (datetime): When webhook was received.
        processed_at (datetime): When webhook processing completed.
        analysis_id (int): Foreign key to analyses table if applicable.
        analysis: Relationship to Analyses model.
    """

    __tablename__ = 'webhooks'

    id: Mapped[int] = mapped_column(primary_key=True)
    gitlab_event_uuid: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False
    )
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(
        String,
        default="received",
        nullable=False
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False
    )
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("analyses.id"),
        nullable=True,
        unique=True
    )

    # Relationships
    analysis: Mapped["Analyses"] = relationship(
        "Analyses",
        back_populates="webhook"
    )
