"""
Git synchronization manager for AI Employee vault.

Handles Git operations for syncing vault between Cloud and Local agents.
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import git
from git.exc import GitCommandError

from app.error_recovery import (
    TransientError,
    AuthenticationError,
    ErrorLogger,
    with_retry
)
from app.vault_sync.conflict_resolver import ConflictResolver

logger = logging.getLogger("vault_sync.git_manager")


class GitManager:
    """Manages Git operations for vault synchronization."""

    def __init__(self, vault_path: str, agent_name: str = "local-agent"):
        """
        Initialize GitManager.

        Args:
            vault_path: Absolute path to vault directory
            agent_name: Name of agent performing operations
        """
        self.vault_path = Path(vault_path)
        self.agent_name = agent_name
        self.repo: Optional[git.Repo] = None
        self.error_logger = ErrorLogger()
        self.conflict_resolver: Optional[ConflictResolver] = None
        self._initialize_repo()

    def _initialize_repo(self) -> None:
        """Initialize Git repository connection."""
        try:
            self.repo = git.Repo(self.vault_path)
            self.conflict_resolver = ConflictResolver(str(self.vault_path))
            logger.info(f"Initialized Git repo at {self.vault_path}")
        except git.exc.InvalidGitRepositoryError as e:
            logger.error(f"Not a valid Git repository: {self.vault_path}")
            self.error_logger.log_error(
                component="GitManager",
                error_type="SYSTEM",
                message=f"Invalid Git repository: {self.vault_path}",
                error=e
            )
            raise ValueError(f"Invalid Git repository: {self.vault_path}")
        except Exception as e:
            logger.error(f"Failed to initialize Git repository: {e}")
            self.error_logger.log_error(
                component="GitManager",
                error_type="SYSTEM",
                message="Failed to initialize Git repository",
                error=e
            )
            raise

    def sync_vault(
        self,
        commit_message: str,
        max_retries: int = 3,
        retry_delay: int = 5
    ) -> Dict:
        """
        Perform full sync cycle: pull, commit, push.

        Args:
            commit_message: Commit message following [agent] action domain: description
            max_retries: Maximum number of retry attempts for network operations
            retry_delay: Delay in seconds between retries

        Returns:
            Dict with sync results including commits_pulled, commits_pushed, files_changed
        """
        start_time = time.time()
        logger.info(f"Starting vault sync for {self.agent_name}")

        try:
            # Pull latest changes
            pull_result = self._pull_with_retry(max_retries, retry_delay)
            commits_pulled = pull_result.get("commits_pulled", 0)

            # Commit local changes if any
            files_changed = self._commit_changes(commit_message)

            # Push to remote
            push_result = self._push_with_retry(max_retries, retry_delay)
            commits_pushed = push_result.get("commits_pushed", 0)

            sync_duration_ms = int((time.time() - start_time) * 1000)

            result = {
                "success": True,
                "commits_pulled": commits_pulled,
                "commits_pushed": commits_pushed,
                "files_changed": files_changed,
                "sync_duration_ms": sync_duration_ms
            }

            # Log performance metrics with structured logging
            logger.info(
                f"Sync completed successfully",
                extra={
                    "operation": "sync_vault",
                    "operation_duration_ms": sync_duration_ms,
                    "files_processed": len(files_changed),
                    "success_rate": 1.0,
                    "agent_name": self.agent_name,
                    "commits_pulled": commits_pulled,
                    "commits_pushed": commits_pushed
                }
            )
            return result

        except Exception as e:
            sync_duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"Sync failed: {e}",
                extra={
                    "operation": "sync_vault",
                    "operation_duration_ms": sync_duration_ms,
                    "files_processed": 0,
                    "success_rate": 0.0,
                    "agent_name": self.agent_name,
                    "error": str(e)
                }
            )
            raise

    def pull_changes(self, rebase: bool = True) -> Dict:
        """
        Pull latest changes from remote repository.

        Args:
            rebase: Use rebase instead of merge

        Returns:
            Dict with pull results

        Raises:
            AuthenticationError: If authentication fails
            TransientError: If network failure occurs (retryable)
            ValueError: If repository not initialized
        """
        logger.info("Pulling changes from remote")

        try:
            if not self.repo:
                raise ValueError("Repository not initialized")

            # Fetch from remote
            origin = self.repo.remote("origin")
            fetch_info = origin.fetch()

            # Get current branch
            current_branch = self.repo.active_branch.name

            # Pull with rebase or merge
            if rebase:
                self.repo.git.pull("--rebase", "origin", current_branch)
            else:
                self.repo.git.pull("origin", current_branch)

            # Check for merge conflicts
            if self.conflict_resolver and self.conflict_resolver.get_conflicts():
                conflicts = self.conflict_resolver.get_conflicts()
                logger.warning(f"Merge conflicts detected: {len(conflicts)} files")

                # Attempt to auto-resolve conflicts
                resolved_count = 0
                for conflict in conflicts:
                    try:
                        strategy = conflict.get("resolution_strategy", "manual")
                        if strategy != "manual":
                            self.conflict_resolver.resolve_conflict(
                                conflict["file"],
                                strategy=strategy
                            )
                            resolved_count += 1
                    except Exception as resolve_error:
                        logger.warning(f"Could not auto-resolve {conflict['file']}: {resolve_error}")

                if resolved_count < len(conflicts):
                    # Some conflicts require manual resolution
                    unresolved = [c["file"] for c in conflicts if c.get("resolution_strategy") == "manual"]
                    logger.error(f"Manual conflict resolution required for: {unresolved}")
                    self.error_logger.log_error(
                        component="GitManager",
                        error_type="DATA",
                        message=f"Merge conflicts require manual resolution: {unresolved}",
                        context={"conflicts": conflicts}
                    )
                    return {
                        "success": False,
                        "error": "merge_conflicts",
                        "conflicts": conflicts,
                        "message": f"Manual resolution required for {len(unresolved)} files"
                    }

            # Get list of updated files
            files_updated = [item.a_path for item in fetch_info]

            result = {
                "success": True,
                "commits_pulled": len(fetch_info),
                "files_updated": files_updated
            }

            logger.info(f"Pull completed: {result}")
            return result

        except GitCommandError as e:
            error_msg = str(e).lower()

            # Check for authentication errors
            if any(auth_keyword in error_msg for auth_keyword in [
                "authentication failed", "permission denied", "invalid credentials",
                "could not read from remote", "fatal: authentication"
            ]):
                logger.error(f"Authentication failed during pull: {e}")
                self.error_logger.log_error(
                    component="GitManager",
                    error_type="AUTHENTICATION",
                    message="Git authentication failed - check credentials and access tokens",
                    error=e,
                    context={"operation": "pull", "remote": "origin"}
                )
                raise AuthenticationError(
                    service="Git",
                    message="Authentication failed. Please verify your Git credentials and access tokens."
                )

            # Check for network errors (retryable)
            elif any(net_keyword in error_msg for net_keyword in [
                "network", "timeout", "connection", "could not resolve host",
                "failed to connect", "temporary failure"
            ]):
                logger.warning(f"Network error during pull (retryable): {e}")
                self.error_logger.log_error(
                    component="GitManager",
                    error_type="TRANSIENT",
                    message="Network failure during pull - will retry",
                    error=e,
                    context={"operation": "pull"}
                )
                raise TransientError(f"Network failure during pull: {e}")

            # Other Git errors
            else:
                logger.error(f"Pull failed: {e}")
                self.error_logger.log_error(
                    component="GitManager",
                    error_type="SYSTEM",
                    message="Git pull operation failed",
                    error=e,
                    context={"operation": "pull"}
                )
                raise

        except Exception as e:
            logger.error(f"Unexpected error during pull: {e}")
            self.error_logger.log_error(
                component="GitManager",
                error_type="SYSTEM",
                message="Unexpected error during pull",
                error=e
            )
            raise

    def push_changes(self, force: bool = False) -> Dict:
        """
        Push local changes to remote repository.

        Args:
            force: Force push (use with caution)

        Returns:
            Dict with push results

        Raises:
            AuthenticationError: If authentication fails
            TransientError: If network failure occurs (retryable)
            ValueError: If repository not initialized
        """
        logger.info("Pushing changes to remote")

        try:
            if not self.repo:
                raise ValueError("Repository not initialized")

            origin = self.repo.remote("origin")
            current_branch = self.repo.active_branch.name

            # Push to remote
            if force:
                logger.warning("Force push requested - use with caution")
                push_info = origin.push(current_branch, force=True)
            else:
                push_info = origin.push(current_branch)

            commits_pushed = len(push_info)

            result = {
                "success": True,
                "commits_pushed": commits_pushed
            }

            logger.info(f"Push completed: {result}")
            return result

        except GitCommandError as e:
            error_msg = str(e).lower()

            # Check for authentication errors
            if any(auth_keyword in error_msg for auth_keyword in [
                "authentication failed", "permission denied", "invalid credentials",
                "could not read from remote", "fatal: authentication", "access denied"
            ]):
                logger.error(f"Authentication failed during push: {e}")
                self.error_logger.log_error(
                    component="GitManager",
                    error_type="AUTHENTICATION",
                    message="Git authentication failed - check credentials and access tokens",
                    error=e,
                    context={"operation": "push", "remote": "origin"}
                )
                raise AuthenticationError(
                    service="Git",
                    message="Authentication failed. Please verify your Git credentials and access tokens."
                )

            # Check for network errors (retryable)
            elif any(net_keyword in error_msg for net_keyword in [
                "network", "timeout", "connection", "could not resolve host",
                "failed to connect", "temporary failure"
            ]):
                logger.warning(f"Network error during push (retryable): {e}")
                self.error_logger.log_error(
                    component="GitManager",
                    error_type="TRANSIENT",
                    message="Network failure during push - will retry",
                    error=e,
                    context={"operation": "push"}
                )
                raise TransientError(f"Network failure during push: {e}")

            # Other Git errors
            else:
                logger.error(f"Push failed: {e}")
                self.error_logger.log_error(
                    component="GitManager",
                    error_type="SYSTEM",
                    message="Git push operation failed",
                    error=e,
                    context={"operation": "push"}
                )
                raise

        except Exception as e:
            logger.error(f"Unexpected error during push: {e}")
            self.error_logger.log_error(
                component="GitManager",
                error_type="SYSTEM",
                message="Unexpected error during push",
                error=e
            )
            raise

    def get_sync_status(self) -> Dict:
        """
        Get current sync status of vault.

        Returns:
            Dict with sync status information

        Raises:
            ValueError: If repository not initialized
        """
        try:
            if not self.repo:
                raise ValueError("Repository not initialized")

            # Check for uncommitted changes
            uncommitted_files = [item.a_path for item in self.repo.index.diff(None)]
            uncommitted_files.extend([item.a_path for item in self.repo.index.diff("HEAD")])
            uncommitted_files.extend(self.repo.untracked_files)

            # Get commits ahead/behind remote
            try:
                origin = self.repo.remote("origin")
                origin.fetch()
                current_branch = self.repo.active_branch.name
                commits_behind = len(list(self.repo.iter_commits(f"{current_branch}..origin/{current_branch}")))
                commits_ahead = len(list(self.repo.iter_commits(f"origin/{current_branch}..{current_branch}")))
            except GitCommandError as e:
                error_msg = str(e).lower()

                # Check for authentication errors
                if any(auth_keyword in error_msg for auth_keyword in [
                    "authentication failed", "permission denied", "invalid credentials"
                ]):
                    logger.warning(f"Authentication error while fetching remote status: {e}")
                    self.error_logger.log_error(
                        component="GitManager",
                        error_type="AUTHENTICATION",
                        message="Cannot fetch remote status - authentication required",
                        error=e,
                        context={"operation": "get_sync_status"}
                    )
                # Check for network errors
                elif any(net_keyword in error_msg for net_keyword in [
                    "network", "timeout", "connection", "could not resolve host"
                ]):
                    logger.warning(f"Network error while fetching remote status: {e}")
                    self.error_logger.log_error(
                        component="GitManager",
                        error_type="TRANSIENT",
                        message="Cannot fetch remote status - network issue",
                        error=e,
                        context={"operation": "get_sync_status"}
                    )
                else:
                    logger.warning(f"Could not determine remote status: {e}")

                commits_behind = 0
                commits_ahead = 0
            except Exception as e:
                logger.warning(f"Could not determine remote status: {e}")
                commits_behind = 0
                commits_ahead = 0

            return {
                "has_uncommitted_changes": len(uncommitted_files) > 0,
                "uncommitted_files": uncommitted_files,
                "commits_behind": commits_behind,
                "commits_ahead": commits_ahead
            }

        except Exception as e:
            logger.error(f"Failed to get sync status: {e}")
            self.error_logger.log_error(
                component="GitManager",
                error_type="SYSTEM",
                message="Failed to get sync status",
                error=e
            )
            raise

    def _commit_changes(self, commit_message: str) -> List[str]:
        """
        Commit local changes with formatted message.

        Args:
            commit_message: Commit message to use

        Returns:
            List of files changed in the commit

        Raises:
            ValueError: If repository not initialized
        """
        try:
            if not self.repo:
                raise ValueError("Repository not initialized")

            # Check for changes
            if not self.repo.is_dirty(untracked_files=True):
                logger.info("No changes to commit")
                return []

            # Add all changes (respecting .gitignore)
            self.repo.git.add(A=True)

            # Format commit message with agent name
            formatted_message = f"[{self.agent_name}] {commit_message}"

            # Commit
            commit = self.repo.index.commit(formatted_message)
            files_changed = list(commit.stats.files.keys())

            logger.info(f"Committed {len(files_changed)} files: {commit.hexsha[:7]}")
            return files_changed

        except GitCommandError as e:
            logger.error(f"Commit failed: {e}")
            self.error_logger.log_error(
                component="GitManager",
                error_type="SYSTEM",
                message="Git commit operation failed",
                error=e,
                context={"operation": "commit", "message": commit_message}
            )
            raise

        except Exception as e:
            logger.error(f"Unexpected error during commit: {e}")
            self.error_logger.log_error(
                component="GitManager",
                error_type="SYSTEM",
                message="Unexpected error during commit",
                error=e
            )
            raise

    def _pull_with_retry(self, max_retries: int, retry_delay: int) -> Dict:
        """
        Pull with exponential backoff retry logic.

        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay in seconds between retries

        Returns:
            Dict with pull results

        Raises:
            AuthenticationError: If authentication fails (not retried)
            GitCommandError: If pull fails after all retries
        """
        for attempt in range(max_retries):
            try:
                return self.pull_changes()
            except AuthenticationError:
                # Authentication errors should not be retried
                logger.error("Authentication error during pull - immediate failure")
                raise
            except TransientError as e:
                # Network errors should be retried
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    logger.warning(f"Transient error during pull (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Pull failed after {max_retries} attempts due to transient errors")
                    raise
            except GitCommandError as e:
                # Other Git errors - retry with backoff
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    logger.warning(f"Pull failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Pull failed after {max_retries} attempts")
                    raise
            except Exception as e:
                # Unexpected errors - don't retry
                logger.error(f"Unexpected error during pull: {e}")
                raise

    def _push_with_retry(self, max_retries: int, retry_delay: int) -> Dict:
        """
        Push with exponential backoff retry logic.

        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay in seconds between retries

        Returns:
            Dict with push results

        Raises:
            AuthenticationError: If authentication fails (not retried)
            GitCommandError: If push fails after all retries
        """
        for attempt in range(max_retries):
            try:
                return self.push_changes()
            except AuthenticationError:
                # Authentication errors should not be retried
                logger.error("Authentication error during push - immediate failure")
                raise
            except TransientError as e:
                # Network errors should be retried
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    logger.warning(f"Transient error during push (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Push failed after {max_retries} attempts due to transient errors")
                    raise
            except GitCommandError as e:
                # Other Git errors - retry with backoff
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    logger.warning(f"Push failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Push failed after {max_retries} attempts")
                    raise
            except Exception as e:
                # Unexpected errors - don't retry
                logger.error(f"Unexpected error during push: {e}")
                raise
