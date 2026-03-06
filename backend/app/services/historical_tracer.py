"""Historical context tracer for commits.

This module traces commits back through their MRs and issues to understand
the historical context and reasoning behind code changes.
"""

from app.logger import logger
from app.services.gitlab_client import GitlabClient


class HistoricalTracer:
    """Traces commits to their historical context.

    Given a commit, finds:
    - Which MR introduced it
    - What issue that MR was solving
    - What was discussed in the MR

    Attributes:
        MAX_ISSUES (int): Maximum number of linked issues to fetch per MR.
        gitlab (GitlabClient): GitLab API client instance.
    """

    MAX_ISSUES = 3

    def __init__(self):
        """Initialize with GitLab client."""
        self.gitlab = GitlabClient()

    def trace_commit_history(self, project_id: int, commit_sha: str):
        """Trace a commit back to its full historical context.

        Args:
            project_id (int): GitLab project ID.
            commit_sha (str): The commit hash to trace.

        Returns:
            dict: Historical context with keys:
                - commit: Commit details (message, author, sha)
                - mr: MR that introduced this commit (or None)
                - issues: List of issues the MR was solving (or empty list)
                - discussion: Key comments from the MR (or empty list)
        """
        # Get commit history
        logger.info(f"Tracing history for commit {commit_sha[:8]}")

        commit = self.gitlab.get_commit(project_id, commit_sha)

        result = {
            'commit': {
                'sha': commit_sha,
                'message': commit['message'],
                'author': commit['author']
            },
            'mr': None,
            'issue': None,
            'discussion': []
        }

        # Find MRs that contain this commit
        mrs = self.gitlab.get_commit_mrs(project_id, commit_sha)
        if not mrs:
            logger.warning(f"No MR found for commit {commit_sha[:8]}")
            return result
        
        # Pick the first merged MR (the original one)
        # Sort by merged_at to get the earliest
        merged_mrs = [mr for mr in mrs if mr['state'] == 'merged' and mr['merged_at']]

        if not merged_mrs:
            # No merged MRs, use the first one anyway
            target_mr = mrs[0]
        else:
            # Use the earliest merged MR
            target_mr = sorted(merged_mrs, key=lambda x: x['merged_at'])[0]
        
        logger.info(f"Found MR !{target_mr['iid']}: {target_mr['title']}")

        # Get full MR details (to get linked issues)
        mr_details = self.gitlab.get_mr_details(project_id, target_mr['iid'])
        result['mr'] = {
            'iid': target_mr['iid'],
            'title': target_mr['title'],
            'description': target_mr['description'],
            'state': target_mr['state'],
            'merged_at': target_mr['merged_at'],
            'web_url': target_mr['web_url']
        }

        # Get the linked issue (if any)
        linked_issue_iids = mr_details.get('linked_issue_iids', [])

        issues = []

    
        if linked_issue_iids:
            # Limit to MAX_ISSUES to keep prompt manageable
            issue_to_fetch = linked_issue_iids[:MAX_ISSUES]

            if len(linked_issue_iids) > MAX_ISSUES:
                logger.warning(
                    f"MR has {len(linked_issue_iids)} linked issues, "
                    f"limiting to {MAX_ISSUES}"
                )

            for issue_iid in issue_to_fetch:
                try:
                    issue = self.gitlab.get_issue(project_id, issue_iid)
                    issues.append({
                        'iid': issue_iid,
                        'title': issue['title'],
                        'description': issue['description'],
                    })
                    logger.info(f"Found linked issue #{issue_iid}: {issue['title']}")
                except Exception as e:
                    logger.error(f"Failed to fetch issue #{issue_iid}: {e}")
                    # Continue with other issues even if one fails
                    continue
            logger.info(f"Fetched {len(issues)} issue(s) total")
        else:
            logger.info("No linked issues found")

        result['issues'] = issues  # Note: plural, not singular

        # Get MR discussion (notes)
        notes = self.gitlab.get_mr_notes(project_id, target_mr['iid'], max_notes=10)

        result['discussion'] = notes

        logger.info(f"Found {len(notes)} discussion notes(s)")

        return result

