# app/tasks/analysis
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
from app.services.analysis_service import extract_relevant_commits
from app.services.claude_client import ClaudeClient
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.design_ratinale import DesignRationales

from app.services.historical_tracer import HistoricalTracer

import hashlib


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
                async with AsyncSessionLocal as failed_session:
                    await _mark_failed(failed_session, analysis_id, str(exc))
                raise

            # Step 3: fetch MR details
            try:
                mr_details = gl.get_mr_details(project_id, mr_iid)
                logger.info(f"Fetched MR details: '{mr_details['title']}'")
                logger.info(
                    f"Found {len(mr_details['linked_issue_iids'])} "
                    f"linked issues"
                )

                # Fetch actual issue content
                linked_issues = []
                for issue_iid in mr_details.get('linked_issue_iids', []):
                    try:
                        issue = gl.get_issue(project_id, issue_iid)
                        issue['iid'] = issue_iid  # Add the iid to the issue dict
                        linked_issues.append(issue)
                        logger.info(f"Fetched issue #{issue_iid}: '{issue['title']}'")
                    except Exception as e:
                        logger.error(f"Failed to fetch issue #{issue_iid}: {e}")
                        # Continue with other issues even if one fails
                        continue
                
                # Add linked issues to mr_details for Claude
                mr_details['linked_issues'] = linked_issues
                logger.info(f"Successfully fetched {len(linked_issues)} issue(s)")

            except Exception as exc:
                logger.error(
                    'Error fetching MR details',
                    exc_info=True
                )
                async with AsyncSessionLocal as failed_session:
                    await _mark_failed(failed_session, analysis_id, str(exc))
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

            # Extract relevant commits for the ENTIRE MR (not per-file)
            logger.info("Extracting relevant commits for entire MR")

            relevant_commits = extract_relevant_commits(
                mr_changes,
                blame_data,
                commit_details,
                max_commits=10
            )

            logger.info(f"Found {len(relevant_commits)} relevant commit(s)")

            # Trace historical context for each relevant commit
            tracer = HistoricalTracer()
            enriched_commits = []

            for commit in relevant_commits:
                try:
                    # Trace the full history of this commit
                    history = tracer.trace_commit_history(project_id, commit['sha'])

                    # Add hsitorical context to the commit
                    enriched_commit = {
                        'sha': commit['sha'],
                        'message': commit['message'],
                        'author_name': commit['author'],
                        'historical_context': {
                            'mr': history.get('mr'),
                            'issues': history.get('issues', []),
                            'discussion': history.get('discussion', [])
                        }
                    }

                    enriched_commits.append(enriched_commit)

                    if history.get('mr'):
                        logger.info(
                            f"Commit {commit['sha'][:8]} has historical context "
                            f"from MR !{history['mr']['iid']}"
                        )
                    else:
                        logger.info(f"Commit {commit['sha'][:8]} has no MR history")
                except Exception as e:
                    logger.info(f"Failed to trace history for {commit['sha'][:8]}: {e}")
                    # Continue without historical context for this commit
                    enriched_commits.append({
                        'sha': commit['sha'],
                        'message': commit['message'],
                        'author_name': commit['author'],
                        'historical_context': None
                        })
            logger.info(f"Enriched {len(enriched_commits)} commit(s) with historical context")

            # Call claude once for the entire MR
            claude = ClaudeClient()

            logger.info("Calling Claude for MR analysis")

            claude_result = claude.analyze_historical_context(
                mr_details,
                enriched_commits
            )

            # Determine action based on confidence

            confidence = claude_result.get('confidence', 0.0)
            if confidence >= 0.90:
                action = "block"
            elif confidence >= 0.70:
                action = "warning"
            elif confidence >= 0.50:
                action = "info"
            else:
                action = "skip"
            

            # Save to DesignRationales table
            
            # Create a summary of all changed files
            files_changed = ", ".join([c['new_path'] for c in mr_changes[:5]])
            if len(mr_changes) > 5:
                files_changed += f" and {len(mr_changes) - 5} more files"
            
            stmt = pg_insert(DesignRationales).values(
                analysis_id=analysis_id,
                what=claude_result.get('what'),
                why=claude_result.get('why'),
                context=claude_result.get('context'),
                tradeoffs=claude_result.get('tradeoffs'),
                rationale_found=claude_result.get('rationale_found', False),
                confidence=confidence,
                action_taken=action,
                file_path=files_changed,  # Summary of files
                content_hash=None,  # Not needed for MR-level analysis
            )

            await session.execute(stmt)

            # Save acceptance criteria to Analyses table
            acceptance_criteria_result = {
                'alignment': claude_result.get('alignment'),
                'rationale_found': claude_result.get('rationale_found'),
                'confidence': confidence
            }


            # Step 6: update analysis status to "completed"
            stmt = update(Analyses).where(
                Analyses.id == analysis_id
            ).values(
                action=action,
                confidence_score=confidence,
                acceptance_criteria=acceptance_criteria_result,
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
                async with AsyncSessionLocal as failed_session:
                    await _mark_failed(failed_session, analysis_id, str(exc))
            except Exception as db_exc:
                await failed_session.rollback()
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
