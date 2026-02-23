"""
Domain configuration loader for AI Employee vault.

Manages domain definitions and access control rules.
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("vault_sync.domain_config")


class DomainConfig:
    """Loads and manages domain configuration from domains.yaml."""

    def __init__(self, vault_path: str):
        """
        Initialize DomainConfig.

        Args:
            vault_path: Absolute path to vault directory
        """
        self.vault_path = Path(vault_path)
        self.config_path = self.vault_path / ".config" / "domains.yaml"
        self.domains: Dict = {}
        self.agents: Dict = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load domain configuration from YAML file."""
        if not self.config_path.exists():
            logger.error(
                f"[CONFIG_LOAD_FAILED] operation=load_config "
                f"reason=file_not_found path={self.config_path}"
            )
            raise FileNotFoundError(f"Domain configuration not found: {self.config_path}")

        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)

            self.domains = config.get("domains", {})
            self.agents = config.get("agents", {})

            logger.info(
                f"[CONFIG_LOADED] operation=load_config "
                f"domains_count={len(self.domains)} agents_count={len(self.agents)}"
            )

        except Exception as e:
            logger.error(
                f"[CONFIG_LOAD_FAILED] operation=load_config "
                f"error={str(e)}"
            )
            raise

    def get_domain(self, domain_name: str) -> Optional[Dict]:
        """
        Get configuration for a specific domain.

        Args:
            domain_name: Name of the domain (e.g., "email", "social", "local-only")

        Returns:
            Domain configuration dict or None if not found
        """
        return self.domains.get(domain_name)

    def get_all_domains(self) -> List[str]:
        """
        Get list of all configured domain names.

        Returns:
            List of domain names
        """
        return list(self.domains.keys())

    def get_agent_config(self, agent_name: str) -> Optional[Dict]:
        """
        Get configuration for a specific agent.

        Args:
            agent_name: Name of the agent (e.g., "cloud-agent", "local-agent")

        Returns:
            Agent configuration dict or None if not found
        """
        return self.agents.get(agent_name)

    def get_allowed_domains(self, agent_name: str) -> List[str]:
        """
        Get list of domains an agent is allowed to access.

        Args:
            agent_name: Name of the agent

        Returns:
            List of allowed domain names
        """
        agent_config = self.get_agent_config(agent_name)
        if not agent_config:
            logger.warning(f"Agent not found in configuration: {agent_name}")
            return []

        return agent_config.get("allowed_domains", [])

    def is_cloud_accessible(self, domain_name: str) -> bool:
        """
        Check if a domain is accessible from cloud agent.

        Args:
            domain_name: Name of the domain

        Returns:
            True if cloud accessible, False otherwise
        """
        domain = self.get_domain(domain_name)
        if not domain:
            return False

        return domain.get("cloud_access", False)

    def is_local_accessible(self, domain_name: str) -> bool:
        """
        Check if a domain is accessible from local agent.

        Args:
            domain_name: Name of the domain

        Returns:
            True if local accessible, False otherwise
        """
        domain = self.get_domain(domain_name)
        if not domain:
            return False

        return domain.get("local_access", False)

    def requires_approval(self, domain_name: str) -> bool:
        """
        Check if a domain requires approval before execution.

        Args:
            domain_name: Name of the domain

        Returns:
            True if approval required, False otherwise
        """
        domain = self.get_domain(domain_name)
        if not domain:
            return True  # Default to requiring approval for safety

        return domain.get("requires_approval", True)

    def get_approval_threshold(self, domain_name: str) -> str:
        """
        Get approval threshold for a domain.

        Args:
            domain_name: Name of the domain

        Returns:
            Approval threshold: "all", "high_priority", or "none"
        """
        domain = self.get_domain(domain_name)
        if not domain:
            return "all"  # Default to requiring approval for all

        return domain.get("approval_threshold", "all")

    def validate_domain(self, domain_name: str) -> bool:
        """
        Validate that a domain exists in configuration.

        Args:
            domain_name: Name of the domain to validate

        Returns:
            True if domain exists, False otherwise
        """
        return domain_name in self.domains

    def reload_config(self) -> None:
        """Reload domain configuration from file."""
        logger.info("Reloading domain configuration")
        self._load_config()
