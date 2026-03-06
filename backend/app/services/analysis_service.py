"""Analysis service for extracting relevant commits from code changes.

This module provides utilities for identifying which commits are relevant
to specific code changes by analyzing diffs and blame information.
"""

import re


def extract_relevant_commits(
    changes,
    blame_data,
    commit_details,
    max_commits=10
):
    """Extract commits relevant to the changed lines in a diff.

    Analyzes file diffs to identify which lines were changed, then uses
    blame data to find the commits that last modified those lines.

    Args:
        changes: List of file change dicts with 'new_path' and 'diff' keys.
        blame_data: Dict mapping file paths to line-number-to-commit-sha maps.
        commit_details: Dict mapping commit SHAs to commit information.
        max_commits (int): Maximum number of commits to return.

    Returns:
        list[dict]: List of relevant commits with sha, message, and author.
            Limited to max_commits entries.
    """
    relevant_sha = set()

    for change in changes:
        file_path = change['new_path']
        diff_text = change['diff']

        # Skip if we have no blame data for this file
        if file_path not in blame_data:
            continue

        # Find which line numbers changed in this diff
        line_number = 0

        for line in diff_text.split('\n'):
            if line.startswith('@@'):
                # Extract starting line number from @@ -old +new @@
                match = re.search(r'\+(\d+)', line)
                if match:
                    line_number = int(match.group(1))
            elif line.startswith('+') and not line.startswith('+++'):
                # This is a new line, check if it's in our blame data
                sha = blame_data[file_path].get(line_number)
                if sha and sha in commit_details:
                    relevant_sha.add(sha)
                line_number += 1
            elif line.startswith('-') and not line.startswith('---'):
                # This line was removed — don't increment line_number
                pass
            else:
                # Context line - just increment
                line_number += 1

    # Collect commit details AFTER processing all files
    relevant_commits = []
    for sha in list(relevant_sha)[:max_commits]:
        commit = commit_details[sha]
        relevant_commits.append({
            "sha": sha,
            "message": commit['message'],
            "author": commit['author']
        })

    return relevant_commits