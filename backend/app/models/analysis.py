"""Analysis model for storing code review analysis results.

This module defines the Analyses table which tracks AI-powered code review
analysis for merge requests, including status, confidence scores, and actions.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Analyses(Base):
    """Analysis results for merge request code reviews.

    Tracks the status, results, and metadata of AI-powered code analysis
    performed on GitLab merge requests.

    Attributes:
        id (int): Primary key.
        mr_id (int): Foreign key to merge_requests table.
        trigger_type (str): How analysis was triggered (webhook/manual).
        status (str): Current status (pending/running/completed/failed).
        confidence_score (float): AI confidence score for the analysis.
        action_taken (str): Action taken based on analysis results.
        acceptance_criteria (dict): JSON criteria used for evaluation.
        gitlab_comment_id (str): ID of comment posted to GitLab.
        gitlab_comment_url (str): URL of comment posted to GitLab.
        error_message (str): Error details if analysis failed.
        started_at (datetime): When analysis started.
        completed_at (datetime): When analysis completed.
        created_at (datetime): When record was created.
        merge_request: Relationship to MergeRequests model.
        webhook: Relationship to Webhooks model.
    """

    __tablename__ = "analyses"
    __table_args__ = (
        Index('idx_analyses_merge_request_id', 'mr_id'),
        Index('idx_analyses_status_created', 'status', 'created_at')
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    mr_id: Mapped[int] = mapped_column(
        ForeignKey("merge_requests.id"),
        nullable=False
    )
    trigger_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=True)
    action_taken: Mapped[str] = mapped_column(String, nullable=True)
    acceptance_criteria: Mapped[dict] = mapped_column(JSONB, nullable=True)
    gitlab_comment_id: Mapped[str] = mapped_column(String, nullable=True)
    gitlab_comment_url: Mapped[str] = mapped_column(String, nullable=True)
    error_message: Mapped[str] = mapped_column(String, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False
    )

    # Relationships
    merge_request: Mapped["MergeRequests"] = relationship(
        "MergeRequests",
        back_populates="analyses"
    )
    webhook: Mapped["Webhooks"] = relationship(
        "Webhooks",
        back_populates="analysis",
        uselist=False
    )




