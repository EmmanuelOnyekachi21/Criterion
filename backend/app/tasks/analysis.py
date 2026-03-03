"""Celery tasks for merge request code analysis.

This module contains background tasks for analyzing GitLab merge requests
using AI-powered code review.
"""

import asyncio

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.logger import logger
from app.models.analysis import Analyses
from app.services.gitlab_client import GitlabClient


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
    try:
        asyncio.run(_run_analysis(project_id, mr_iid, analysis_id))
        logger.info(f"Task completed for analysis {analysis_id}")
    except Exception as exc:
        logger.error(
            f"Task failed for analysis {analysis_id}: {exc}",
            exc_info=True,
            extra={
                "project_id": project_id,
                "mr_iid": mr_iid,
                "analysis_id": analysis_id
            }
        )


async def _run_analysis(
    project_id: int,
    mr_iid: int,
    analysis_id: int
):
    """Execute the analysis workflow asynchronously.

    Fetches MR changes, details, blame information, and commit details,
    then updates the analysis status in the database.

    Args:
        project_id (int): GitLab project ID.
        mr_iid (int): GitLab merge request internal ID.
        analysis_id (int): Database ID of the analysis record.

    Raises:
        Exception: Re-raises any exception after marking analysis as failed.
    """
    async with AsyncSessionLocal() as session:
        try:
            # Step 1: update analysis status to "running"
            stmt = update(Analyses).where(
                Analyses.id == analysis_id
            ).values(
                status="running",
                started_at=func.now()
            )
            await session.execute(stmt)
            await session.commit()

            logger.info(
                f"Analysis {analysis_id} marked as running"
            )

            # Step 2: fetch MR changes
            gl = GitlabClient()

            try:
                mr_changes = gl.get_mr_changes(project_id, mr_iid)
                logger.info(
                    f"Fetched {len(mr_changes)} file changes from "
                    f"MR !{mr_iid}"
                )
            except Exception as exc:
                logger.error(
                    f'Error fetching MR changes: {exc}',
                    exc_info=True
                )
                # Mark analysis as failed
                await _mark_failed(session, analysis_id, str(exc))
                raise

            # Step 3: fetch MR details
            try:
                mr_details = gl.get_mr_details(project_id, mr_iid)
                logger.info(f"Fetched MR details: '{mr_details['title']}'")
                logger.info(
                    f"Found {len(mr_details['linked_issue_iids'])} "
                    f"linked issues"
                )
            except Exception as exc:
                logger.error(
                    'Error fetching MR details',
                    exc_info=True
                )
                await _mark_failed(session, analysis_id, str(exc))
                raise

            # Step 4: for each changed file, get blame
            blame_data = {}
            source_branch = mr_details['source_branch']

            for change in mr_changes:
                file_path = change.get('new_path') or change.get('old_path')

                # Skip deleted files
                if not file_path or change.get('deleted_file'):
                    continue

                try:
                    blame_map = gl.get_blame(
                        project_id,
                        file_path,
                        source_branch
                    )
                    blame_data[file_path] = blame_map
                    logger.info(
                        f"Got blame for {file_path}: {len(blame_map)} lines"
                    )
                except Exception as exc:
                    logger.error(
                        f"Failed to get blame for {file_path}: {exc}"
                    )
                    # Continue with other files even if one fails
                    continue

            logger.info(f"Got blame data for {len(blame_data)} files")

            # Step 5: for each unique commit SHA, get commit details
            unique_shas = set()
            for blame_map in blame_data.values():
                unique_shas.update(blame_map.values())

            logger.info(f"Found {len(unique_shas)} unique commits to fetch")

            commit_details = {}
            for commit_sha in unique_shas:
                try:
                    commit = gl.get_commit(project_id, commit_sha)
                    commit_details[commit_sha] = commit
                    logger.info(f"Fetched commit {commit_sha[:8]}")
                except Exception as exc:
                    logger.error(
                        f"Failed to fetch commit {commit_sha}: {exc}"
                    )
                    continue

            # Step 6: update analysis status to "completed"
            stmt = update(Analyses).where(
                Analyses.id == analysis_id
            ).values(
                status="completed",
                completed_at=func.now()
            )
            await session.execute(stmt)
            await session.commit()
            logger.info("Analysis completed successfully")

        except Exception as exc:
            # If anything fails, mark as failed
            logger.error(
                f"Analysis {analysis_id} failed: {exc}",
                exc_info=True
            )

            await session.rollback()

            # Try to update status to failed
            try:
                await _mark_failed(session, analysis_id, str(exc))
            except Exception as db_exc:
                logger.error(
                    f"Failed to update analysis status: {db_exc}"
                )

            raise


async def _mark_failed(
    session: AsyncSession,
    analysis_id: int,
    error: str
) -> None:
    """Mark an analysis as failed in the database.

    Updates the analysis record with failed status, error message, and
    completion timestamp.

    Args:
        session (AsyncSession): SQLAlchemy async session.
        analysis_id (int): Database ID of the analysis record.
        error (str): Error message to store.

    Returns:
        None
    """
    stmt = update(Analyses).where(
        Analyses.id == analysis_id
    ).values(
        status="failed",
        error_message=str(error),
        completed_at=func.now()
    )
    await session.execute(stmt)
    await session.commit()
