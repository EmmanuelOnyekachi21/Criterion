"""Merge request model for tracking GitLab MR metadata.

This module defines the MergeRequests table which stores information about
GitLab merge requests being analyzed.
"""

from datetime import datetime
from typing import List

from sqlalchemy import DateTime, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MergeRequests(Base):
    """GitLab merge request metadata and tracking.

    Stores information about merge requests from GitLab including project
    details, branch information, and state tracking.

    Attributes:
        id (int): Primary key.
        gitlab_project_id (int): GitLab project ID.
        gitlab_mr_iid (int): GitLab merge request internal ID.
        gitlab_mr_id (int): GitLab merge request global ID.
        project_name (str): Name of the GitLab project.
        project_namespace (str): Namespace/organization of the project.
        title (str): Merge request title.
        author_username (str): Username of the MR author.
        source_branch (str): Source branch name.
        target_branch (str): Target branch name.
        mr_url (str): Full URL to the merge request.
        state (str): Current state (opened/closed/merged/locked).
        gitlab_created_at (datetime): When MR was created in GitLab.
        first_seen_at (datetime): When we first saw this MR.
        last_updated_at (datetime): When record was last updated.
        analyses: Relationship to Analyses model.
    """

    __tablename__ = "merge_requests"
    __table_args__ = (
        Index(
            'idx_merge_requests_project_iid',
            'gitlab_project_id',
            'gitlab_mr_iid',
            unique=True
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    gitlab_project_id: Mapped[int] = mapped_column(Integer, nullable=False)
    gitlab_mr_iid: Mapped[int] = mapped_column(Integer, nullable=False)
    gitlab_mr_id: Mapped[int] = mapped_column(Integer, nullable=False)
    project_name: Mapped[str] = mapped_column(String, nullable=False)
    project_namespace: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    author_username: Mapped[str] = mapped_column(String, nullable=False)
    source_branch: Mapped[str] = mapped_column(String, nullable=False)
    target_branch: Mapped[str] = mapped_column(String, nullable=False)
    mr_url: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[str] = mapped_column(String, nullable=False)
    gitlab_created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False
    )
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    analyses: Mapped[List["Analyses"]] = relationship(
        "Analyses",
        back_populates="merge_request"
    )



