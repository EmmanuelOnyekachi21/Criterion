"""Pydantic schemas for GitLab webhook payload validation.

This module defines Pydantic models for validating and parsing incoming
GitLab webhook payloads with proper type checking.
"""

from typing import Optional

from pydantic import BaseModel


class GitLabUser(BaseModel):
    """GitLab user information from webhook payload.

    Attributes:
        id (int): GitLab user ID.
        name (str): User's display name.
        username (str): User's username.
        avatar_url (Optional): URL to user's avatar image.
    """

    id: int
    name: str
    username: str
    avatar_url: Optional[str] = None


class GitLabProject(BaseModel):
    """GitLab project information from webhook payload.

    Attributes:
        id (int): GitLab project ID.
        name (str): Project name.
        web_url (str): Full URL to the project.
        path_with_namespace (str): Full path like "org/my-project".
    """

    id: int
    name: str
    web_url: str
    path_with_namespace: str


class MergeRequestAttributes(BaseModel):
    """Merge request attributes from webhook payload.

    Attributes:
        id (int): GitLab merge request global ID.
        iid (int): GitLab merge request internal ID.
        title (str): Merge request title.
        description (Optional[str]): Merge request description.
        state (str): Current state (opened/closed/merged/locked).
        url (str): Full URL to the merge request.
        source_branch (str): Source branch name.
        target_branch (str): Target branch name.
        action (Optional[str]): Action type (open/update/merge/close).
        created_at (Optional[str]): ISO timestamp of creation.
    """

    id: int
    iid: int
    title: str
    description: Optional[str] = None
    state: str
    url: str
    source_branch: str
    target_branch: str
    action: Optional[str] = None
    created_at: Optional[str] = None


class GitLabWebhookPayload(BaseModel):
    """Complete GitLab webhook payload structure.

    Attributes:
        object_kind (str): Type of object (merge_request, etc).
        event_type (Optional[str]): Specific event type.
        user (GitLabUser): User who triggered the event.
        project (GitLabProject): Project information.
        object_attributes (MergeRequestAttributes): MR details.
    """

    object_kind: str
    event_type: Optional[str] = None
    user: GitLabUser
    project: GitLabProject
    object_attributes: MergeRequestAttributes
