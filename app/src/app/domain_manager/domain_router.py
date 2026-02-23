"""
Domain-based routing for AI Employee vault.

Routes tasks to authorized agents based on domain access rules.
"""

import logging
import time
from pathlib import Path
from typing import List, Optional
from .domain_config import DomainConfig

logger = logging.getLogger("vault_sync.domain_router")


class DomainRouter:
    """Routes tasks based on domain access rules."""

    def __init__(self, vault_path: str, agent_name: str):
        """
        Initialize DomainRouter.

        Args:
            vault_path: Absolute path to vault directory
            agent_name: Name of the agent (e.g., "cloud-agent", "local-agent")
        """
        self.vault_path = Path(vault_path)
        self.agent_name = agent_name
        self.domain_config = DomainConfig(str(vault_path))
        self.allowed_domains = self.domain_config.get_allowed_domains(agent_name)

        logger.info(f"Initialized DomainRouter for {agent_name} with domains: {self.allowed_domains}")

    def can_access_domain(self, domain_name: str) -> bool:
        """
        Check if the agent can access a specific domain.

        Args:
            domain_name: Name of the domain to check

        Returns:
            True if agent can access domain, False otherwise
        """
        # Validate domain exists
        if not self.domain_config.validate_domain(domain_name):
            logger.warning(f"Invalid domain: {domain_name}")
            return False

        # Check if domain is in agent's allowed list
        if domain_name not in self.allowed_domains:
            logger.debug(f"Agent {self.agent_name} cannot access domain: {domain_name}")
            return False

        # Additional check: verify domain allows this agent type
        if self.agent_name.startswith("cloud"):
            if not self.domain_config.is_cloud_accessible(domain_name):
                logger.warning(f"Domain {domain_name} is not cloud accessible")
                return False
        elif self.agent_name.startswith("local"):
            if not self.domain_config.is_local_accessible(domain_name):
                logger.warning(f"Domain {domain_name} is not local accessible")
                return False

        return True

    def get_allowed_domains(self) -> List[str]:
        """
        Get list of domains this agent can access.

        Returns:
            List of allowed domain names
        """
        return self.allowed_domains.copy()

    def filter_tasks_by_domain(self, task_files: List[Path]) -> List[Path]:
        """
        Filter task files to only include those in allowed domains.

        Args:
            task_files: List of task file paths

        Returns:
            Filtered list of task files in allowed domains
        """
        start_time = time.time()
        filtered_tasks = []

        for task_file in task_files:
            # Extract domain from file path
            domain = self._extract_domain_from_path(task_file)

            if domain and self.can_access_domain(domain):
                filtered_tasks.append(task_file)
            else:
                logger.debug(f"Filtered out task (domain: {domain}): {task_file}")

        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"[FILTER_COMPLETE] agent={self.agent_name} operation=filter_tasks_by_domain "
            f"duration_ms={duration_ms} total_tasks={len(task_files)} "
            f"filtered_tasks={len(filtered_tasks)}"
        )
        return filtered_tasks

    def get_domain_directory(self, domain_name: str, status: str = "Needs_Action") -> Optional[Path]:
        """
        Get directory path for a specific domain and status.

        Args:
            domain_name: Name of the domain
            status: Status directory (e.g., "Needs_Action", "In_Progress", "Done")

        Returns:
            Path to domain directory or None if not accessible
        """
        if not self.can_access_domain(domain_name):
            logger.warning(f"Cannot access domain directory: {domain_name}")
            return None

        domain_dir = self.vault_path / status / domain_name

        if not domain_dir.exists():
            logger.warning(f"Domain directory does not exist: {domain_dir}")
            return None

        return domain_dir

    def get_all_accessible_directories(self, status: str = "Needs_Action") -> List[Path]:
        """
        Get all domain directories this agent can access for a given status.

        Args:
            status: Status directory (e.g., "Needs_Action", "In_Progress", "Done")

        Returns:
            List of accessible domain directory paths
        """
        accessible_dirs = []

        for domain in self.allowed_domains:
            domain_dir = self.get_domain_directory(domain, status)
            if domain_dir:
                accessible_dirs.append(domain_dir)

        return accessible_dirs

    def _extract_domain_from_path(self, file_path: Path) -> Optional[str]:
        """
        Extract domain name from file path.

        Args:
            file_path: Path to task file

        Returns:
            Domain name or None if not found
        """
        # Expected path structure: .../Needs_Action/email/task.md
        # or .../In_Progress/cloud-agent/task.md (need to check parent)

        try:
            # Get relative path from vault root
            rel_path = file_path.relative_to(self.vault_path)
            parts = rel_path.parts

            # Check if second part is a domain
            if len(parts) >= 2:
                potential_domain = parts[1]
                if self.domain_config.validate_domain(potential_domain):
                    return potential_domain

            # For In_Progress, domain might be in task metadata
            # This would require reading the file, which we'll handle in file_processor
            return None

        except ValueError:
            logger.warning(f"File path not relative to vault: {file_path}")
            return None

    def validate_task_domain(self, task_metadata: dict) -> bool:
        """
        Validate that a task's domain is accessible by this agent.

        Args:
            task_metadata: Task metadata dict with 'domain' field

        Returns:
            True if task domain is accessible, False otherwise
        """
        domain = task_metadata.get("domain")
        if not domain:
            logger.warning("Task metadata missing domain field")
            return False

        return self.can_access_domain(domain)

    def requires_approval(self, domain_name: str) -> bool:
        """
        Check if tasks in this domain require approval.

        Args:
            domain_name: Name of the domain

        Returns:
            True if approval required, False otherwise
        """
        return self.domain_config.requires_approval(domain_name)
