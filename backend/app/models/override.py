"""Override model for tracking developer overrides with feedback loop.

This module defines the Overrides table which tracks when developers override
AI analysis decisions and captures follow-up feedback for calibration.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text, Boolean, func
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.database import Base


class Overrides(Base):
    """Developer override with feedback loop for AI calibration.

    Tracks when developers override AI analysis decisions, their reasoning,
    and follow-up feedback to determine if the override was justified. This
    enables continous improvement of the AI analysis confidence scoring.

    Attributes:
        id (int): Primary key.
        analysis_id (int): Foreign key to analyses table.
        developer_username (str): Username of developer who overrode.
        override_reason (str): Explanation for the override.
        overridden_at (datetime): When the override occurred.
        acknowledgment_comment_id (str): GitLab comment ID acknowledging override.
        acknowledgment_text (str): Text of acknowledgment comment.
        acknowledged_at (datetime): When acknowledgment was posted.
        follow_up_comment_id (str): GitLab comment ID for follow-up.
        follow_up_sent_at (datetime): When follow-up was sent.
        caused_issue (bool): Whether override caused issues (null until follow-up).
        issue_description (str): Description of any issues that occurred.
        confidence_at_override (float): AI confidence score at time of override.
        analysis: Relationship to Analyses model.
    """

    __tablename__ = "overrides"
    __table_args__ = (
        Index('idx_overrides_analysis_id', 'analysis_id'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
    )
    developer_username: Mapped[str] = mapped_column(String, nullable=False)
    override_reason: Mapped[str] = mapped_column(Text, nullable=False)
    overridden_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False
    )
    acknowledgment_comment_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    acknowledgment_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    follow_up_comment_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    follow_up_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    caused_issue: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)  # null until follow-up received
    issue_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence_at_override: Mapped[float] = mapped_column(Float, nullable=False)  # store for calibration

    # Relationships
    analysis: Mapped["Analyses"] = relationship(
        "Analyses",
        back_populates='overrides',
    )

