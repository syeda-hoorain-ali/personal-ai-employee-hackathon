"""
Parser for Business_Goals.md file.

This module reads and parses the Business_Goals.md file to extract
business metrics, targets, and rules.
"""

import logging
import yaml
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Optional

from .entities import BusinessGoals

logger = logging.getLogger("weekly_audit.business_goals_parser")


class BusinessGoalsParser:
    """
    Parser for extracting business goals from Business_Goals.md.

    The file is expected to have YAML frontmatter containing:
    - revenue_target
    - current_revenue
    - key_metrics
    - active_projects
    - subscription_rules
    - last_updated
    - review_frequency
    """

    def __init__(self, file_path: Path):
        """
        Initialize the parser.

        Args:
            file_path: Path to Business_Goals.md file
        """
        self.file_path = file_path

    def parse(self) -> BusinessGoals:
        """
        Parse the Business_Goals.md file and extract business goals.

        Returns:
            BusinessGoals entity with parsed data

        Raises:
            FileNotFoundError: If Business_Goals.md doesn't exist
            ValueError: If YAML frontmatter is invalid or missing required fields
        """
        if not self.file_path.exists():
            logger.error(f"Business_Goals.md not found at {self.file_path}")
            raise FileNotFoundError(f"Business_Goals.md not found at {self.file_path}")

        logger.info(f"Parsing business goals from {self.file_path}")

        try:
            content = self.file_path.read_text(encoding="utf-8")

            # Extract YAML frontmatter
            if not content.startswith("---"):
                raise ValueError("Business_Goals.md must start with YAML frontmatter (---)")

            # Split content by frontmatter delimiters
            parts = content.split("---", 2)
            if len(parts) < 3:
                raise ValueError("Invalid YAML frontmatter format")

            yaml_content = parts[1].strip()
            data = yaml.safe_load(yaml_content)

            if not data:
                raise ValueError("YAML frontmatter is empty")

            # Parse and validate required fields
            business_goals = BusinessGoals(
                revenue_target=Decimal(str(data["revenue_target"])),
                current_revenue=Decimal(str(data["current_revenue"])),
                key_metrics=data.get("key_metrics", []),
                active_projects=data.get("active_projects", []),
                subscription_rules=data.get("subscription_rules", {
                    "inactivity_days": 30,
                    "cost_increase_threshold": 0.20
                }),
                last_updated=self._parse_date(data["last_updated"]),
                review_frequency=data.get("review_frequency", "weekly")
            )

            logger.info(f"Successfully parsed business goals: revenue_target={business_goals.revenue_target}")
            return business_goals

        except KeyError as e:
            logger.error(f"Missing required field in Business_Goals.md: {e}")
            raise ValueError(f"Missing required field: {e}")
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in Business_Goals.md: {e}")
            raise ValueError(f"Invalid YAML format: {e}")
        except Exception as e:
            logger.error(f"Error parsing Business_Goals.md: {e}")
            raise

    def _parse_date(self, date_str: str) -> date:
        """
        Parse a date string in YYYY-MM-DD format.

        Args:
            date_str: Date string to parse

        Returns:
            date object

        Raises:
            ValueError: If date format is invalid
        """
        try:
            return date.fromisoformat(date_str)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid date format '{date_str}': expected YYYY-MM-DD")
