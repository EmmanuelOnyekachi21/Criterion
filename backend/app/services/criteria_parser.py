"""Parser for extracting acceptance criteria from issue descriptions."""

import re
from typing import List, Optional

from app.logger import logger


class CriteriaParser:
    """Extracts structured acceptance criteria from issue descriptions."""

    def __init__(self):
        """Initialize the parser."""
        pass

    def extract_criteria(self, issue_description: str) -> List[str]:
        """Extract acceptance criteria from issue description.

        Supports multiple formats:
        - Markdown checkboxes: - [ ] criterion
        - Numbered lists: 1. criterion
        - Bullet lists: * criterion or - criterion
        - Section-based: ## Acceptance Criteria followed by list

        Args:
            issue_description (str): The issue description text.

        Returns:
            List[str]: List of criterion strings (empty if none found).
        """
        if not issue_description:
            return []

        criteria = []

        # Strategy 1: Look for "Acceptance Criteria" section
        criteria_section = self._extract_criteria_section(issue_description)
        if criteria_section:
            criteria = self._parse_list_items(criteria_section)

        # Strategy 2: If no section found, look for checkboxes anywhere
        if not criteria:
            criteria = self._extract_checkboxes(issue_description)

        # Strategy 3: If still nothing, look for numbered/bullet lists
        if not criteria:
            criteria = self._extract_lists(issue_description)

        # Clean up criteria
        criteria = [c.strip() for c in criteria if c.strip()]

        logger.info(f"Extracted {len(criteria)} acceptance criteria")
        return criteria

    def _extract_criteria_section(self, text: str) -> Optional[str]:
        """Extract text after 'Acceptance Criteria' header.

        Looks for patterns like:
        - ## Acceptance Criteria
        - **Acceptance Criteria:**
        - Acceptance Criteria:

        Args:
            text (str): The full issue description text.

        Returns:
            Optional[str]: The criteria section text, or None if not found.
        """
        # Pattern: Match "Acceptance Criteria" with optional markdown/formatting
        pattern = (
            r'(?:^|\n)(?:#{1,6}\s*)?(?:\*\*)?Acceptance\s+Criteria'
            r'(?:\*\*)?:?\s*\n(.*?)(?=\n#{1,6}\s|\n\n|\Z)'
        )

        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1)

        return None

    def _parse_list_items(self, text: str) -> List[str]:
        """Parse list items from text (checkboxes, bullets, numbers).

        Args:
            text (str): Text containing list items.

        Returns:
            List[str]: Extracted list items.
        """
        criteria = []

        # Match various list formats
        patterns = [
            r'^\s*-\s*\[[ x]\]\s*(.+)$',  # Markdown checkbox: - [ ] or - [x]
            r'^\s*\d+\.\s*(.+)$',          # Numbered: 1. item
            r'^\s*[-*]\s*(.+)$',           # Bullet: - item or * item
        ]

        for line in text.split('\n'):
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    criteria.append(match.group(1))
                    break

        return criteria

    def _extract_checkboxes(self, text: str) -> List[str]:
        """Extract markdown checkboxes from anywhere in text.

        Args:
            text (str): Text to search for checkboxes.

        Returns:
            List[str]: Extracted checkbox items.
        """
        pattern = r'-\s*\[[ x]\]\s*(.+?)(?=\n|$)'
        matches = re.findall(pattern, text, re.MULTILINE)
        return matches

    def _extract_lists(self, text: str) -> List[str]:
        """Extract numbered or bullet lists from text.

        Args:
            text (str): Text to search for lists.

        Returns:
            List[str]: Extracted list items.
        """
        criteria = []

        # Look for consecutive list items
        lines = text.split('\n')
        in_list = False

        for line in lines:
            # Check if line is a list item
            if re.match(r'^\s*(?:\d+\.|-|\*)\s+.+', line):
                in_list = True
                # Extract the content
                content = re.sub(r'^\s*(?:\d+\.|-|\*)\s+', '', line)
                criteria.append(content)
            elif in_list and line.strip():
                # If we were in a list and hit non-list content, stop
                in_list = False

        return criteria
