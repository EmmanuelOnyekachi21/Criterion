"""Celery tasks for merge request code analysis.

This module contains background tasks for analyzing GitLab merge requests
using AI-powered code review.
"""

from app.celery_app import celery_app


@celery_app.task(name="analyze_merge_request")
def analyze_merge_request(
    project_id: int,
    mr_iid: int,
    analysis_id: int
):
    """Analyze a GitLab merge request asynchronously.

    This task fetches the merge request details, performs AI-powered code
    analysis, and stores the results in the database.

    Args:
        project_id (int): GitLab project ID.
        mr_iid (int): GitLab merge request internal ID.
        analysis_id (int): Database ID of the analysis record.

    Returns:
        None
    """
    pass

