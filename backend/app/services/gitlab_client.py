"""GitLab API client for interacting with merge requests and issues.

This module provides a client wrapper around the python-gitlab library
for fetching merge request changes, issues, blame information, and posting
comments.
"""

import re

from gitlab import Gitlab

from app.config import settings
from app.logger import logger


class GitlabClient:
    """Client for interacting with GitLab API.

    Provides methods for fetching merge request details, file changes,
    blame information, and posting comments to merge requests.

    Attributes:
        token (str): GitLab API token for authentication.
        gl (Gitlab): Initialized python-gitlab client instance.
    """

    def __init__(self):
        """Initialize the GitLab client with credentials from settings."""
        self.token = settings.gitlab_token
        self.gl = Gitlab(
            url=settings.gitlab_url,
            private_token=settings.gitlab_token
        )

    def get_mr_changes(self, project_id: int, mr_iid: int):
        """Fetch file changes (diffs) for a merge request.

        Args:
            project_id (int): GitLab project ID.
            mr_iid (int): Merge request internal ID.

        Returns:
            list[dict]: List of file changes with diff information.
                Each dict contains: old_path, new_path, diff, new_file,
                deleted_file, renamed_file.

        Raises:
            Exception: If fetching MR changes fails.
        """
        try:
            logger.info(
                f"Fetching MR changes from Project {project_id}, "
                f"MR !{mr_iid}"
            )
            # Get project using project id
            project = self.gl.projects.get(id=project_id)

            # Get MR through its iid
            mr = project.mergerequests.get(mr_iid)
            logger.info(
                f"MR '{mr.title}' (State: {mr.state}, "
                f"Branch: {mr.source_branch} → {mr.target_branch})"
            )

            # Get changes (current diff between source and target)
            file_changes = mr.changes()

            return [
                {
                    'old_path': change.get('old_path'),
                    'new_path': change.get('new_path'),
                    'diff': change.get('diff'),
                    'new_file': change.get('new_file'),
                    'deleted_file': change.get('deleted_file'),
                    'renamed_file': change.get('renamed_file')
                }
                for change in file_changes['changes']
            ]
        except Exception as e:
            logger.error(
                f"Failed to get MR changes: {str(e)}",
                exc_info=True
            )
            raise

    def get_issue(self, project_id: int, issue_iid: int):
        """Fetch issue details from a project.

        Args:
            project_id (int): GitLab project ID.
            issue_iid (int): Issue internal ID.

        Returns:
            dict: Issue information with title and description.

        Raises:
            Exception: If fetching issue fails.
        """
        try:
            project = self.gl.projects.get(id=project_id)
            issue = project.issues.get(issue_iid)
            logger.info(f"Issue '{issue.title}' (State: {issue.state})")
            return {
                "title": issue.title,
                "description": issue.description
            }
        except Exception as e:
            logger.error(f'Failed to get issue: {str(e)}', exc_info=True)
            raise

    def get_mr_details(self, project_id: int, mr_iid: int):
        """Fetch detailed merge request information.

        Extracts MR metadata including title, description, branches, and
        linked issue IIDs from the description.

        Args:
            project_id (int): GitLab project ID.
            mr_iid (int): Merge request internal ID.

        Returns:
            dict: MR details including title, description, branches, and
                linked_issue_iids (list of integers).

        Raises:
            Exception: If fetching MR details fails.
        """
        try:
            logger.info(
                f"Fetching MR details from Project {project_id}, "
                f"MR !{mr_iid}"
            )
            # Get project using project id
            project = self.gl.projects.get(id=project_id)

            # Get MR through its iid
            mr = project.mergerequests.get(mr_iid)

            description = mr.description or ""
            linked_issue_iids = re.findall(r'#(\d+)', description)

            return {
                "title": mr.title,
                "description": description,
                "source_branch": mr.source_branch,
                "target_branch": mr.target_branch,
                "linked_issue_iids": [
                    int(n) for n in linked_issue_iids
                ] if linked_issue_iids else []
            }
        except Exception as e:
            logger.error(
                f"Failed to get MR details: {str(e)}",
                exc_info=True
            )
            raise

    def get_blame(self, project_id: int, filepath: str, branch: str):
        """Fetch git blame information for a file.

        Args:
            project_id (int): GitLab project ID.
            filepath (str): Path to the file in the repository.
            branch (str): Branch name to get blame from.

        Returns:
            dict: Mapping of line numbers to commit hashes.

        Raises:
            Exception: If fetching blame information fails.
        """
        try:
            logger.info(
                f"Getting blame for {filepath} at branch {branch} "
                f"in project {project_id}"
            )

            # Get the project
            project = self.gl.projects.get(project_id)

            # Get blame information
            blame_data = project.files.blame(
                file_path=filepath,
                ref=branch
            )

            blame_map = {}
            line_number = 1

            for blame in blame_data:
                for _ in blame['lines']:
                    blame_map[line_number] = blame['commit']['id']
                    line_number += 1

            return blame_map
        except Exception as e:
            logger.error(
                f"Failed to get blame for {filepath}: {str(e)}",
                exc_info=True
            )
            raise

    def get_commit(self, project_id: int, commit_hash: str):
        """Fetch commit details.

        Args:
            project_id (int): GitLab project ID.
            commit_hash (str): Git commit SHA hash.

        Returns:
            dict: Commit information with message and author.

        Raises:
            Exception: If fetching commit fails.
        """
        try:
            logger.info(
                f"Getting commit {commit_hash} in project {project_id}"
            )

            # Get the project
            project = self.gl.projects.get(project_id)

            commit = project.commits.get(commit_hash)

            return {
                "message": commit.message,
                "author": commit.author_name
            }

        except Exception as e:
            logger.error(
                f"Failed to get commit {commit_hash}: {str(e)}",
                exc_info=True
            )
            raise

    def post_mr_comment(self, project_id: int, mr_iid: int, body: str):
        """Post a comment to a merge request.

        Args:
            project_id (int): GitLab project ID.
            mr_iid (int): Merge request internal ID.
            body (str): Comment text to post.

        Returns:
            dict: Posted comment information with note_id and web_url.

        Raises:
            Exception: If posting comment fails.
        """
        try:
            logger.info(
                f"Posting comment to MR !{mr_iid} in project {project_id}"
            )

            # Get the project
            project = self.gl.projects.get(id=project_id)

            # Get the merge request
            mr = project.mergerequests.get(mr_iid)

            # Create a note (comment) on the MR
            note = mr.notes.create({'body': body})

            logger.info(f"Comment posted successfully (note ID: {note.id})")

            return {
                'note_id': note.id,
                'web_url': note.web_url if hasattr(note, 'web_url') else None
            }
        except Exception as e:
            logger.error(
                f"Failed to post comment to MR !{mr_iid}: {str(e)}",
                exc_info=True
            )
            raise

        