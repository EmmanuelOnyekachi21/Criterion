"""Design rationale model for storing historical design context.

This module defines the DesignRationales table which tracks extracted design
decisions, rationale, and context from code analysis.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DesignRationales(Base):
    """Design rationale and context for code changes.

    Stores extracted design decisions, rationale, and historical context
    from AI analysis of merge requests and commits.

    Attributes:
        id (int): Primary key.
        analysis_id (int): Foreign key to analyses table.
        filepath (str): Path to the file containing this design decision.
        function_name (str): Name of the function (if applicable).
        class_name (str): Name of the class (if applicable).
        content_hash (str): Stable identifier for the code section.
        what (str): What technical changes were made.
        why (str): Why the changes were made (rationale).
        context (str): Background context or requirement.
        tradeoffs (str): Alternatives or limitations considered.
        rationale_found (bool): Whether clear rationale was found.
        source_mr_iid (int): MR that introduced this code.
        source_issue_iid (int): Issue that drove this change.
        source_commit_sha (str): Commit that made this change.
        confidence (float): AI confidence score for this analysis.
        created_at (datetime): When record was created.
        analysis: Relationship to Analyses model.
    """

    __tablename__ = 'design_rationales'
    __table_args__ = (
        Index('idx_design_rationales_analysis_id', 'analysis_id'),
        Index('idx_design_rationales_file_path', 'filepath'),
        Index('idx_design_rationales_content_hash', 'content_hash'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("analyses.id"),
        nullable=False
    )
    filepath: Mapped[str] = mapped_column(String, nullable=False)
    function_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    class_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    what: Mapped[str] = mapped_column(Text, nullable=False)
    why: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tradeoffs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rationale_found: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    source_mr_iid: Mapped[Optional[int]] = mapped_column(nullable=True)
    source_issue_iid: Mapped[Optional[int]] = mapped_column(nullable=True)
    source_commit_sha: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False
    )

    # Relationships
    analysis: Mapped["Analyses"] = relationship(
        "Analyses",
        back_populates="design_rationales"
    )