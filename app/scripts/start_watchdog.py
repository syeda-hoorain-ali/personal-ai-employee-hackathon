#!/usr/bin/env python3
"""
Watchdog entry point script.

This script starts the watchdog process that monitors and restarts crashed components.
It can be run manually or scheduled to start automatically on system boot.
"""

import sys
import signal
import logging
import argparse
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.error_recovery.watchdog import Watchdog, ComponentConfig
from app.error_recovery.error_logger import ErrorLogger


def setup_logging(log_level: str = "INFO"):
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                Path.home() / "watchdog.log",
                mode='a'
            )
        ]
    )


def create_component_configs(vault_path: Path) -> list[ComponentConfig]:
    """
    Create component configurations for monitoring.

    Args:
        vault_path: Path to AI_Employee_Vault

    Returns:
        List of ComponentConfig objects
    """
    configs = []

    # Example: GmailWatcher component
    # In production, this would start the actual watcher process
    def start_gmail_watcher() -> int:
        """Start Gmail watcher and return PID."""
        # This is a placeholder - in production, this would:
        # 1. Start the gmail_watcher.py as a subprocess
        # 2. Return the process PID
        # For now, return 0 to indicate not implemented
        logging.warning("GmailWatcher start command not implemented - placeholder only")
        return 0

    def check_gmail_watcher_health() -> bool:
        """Check if Gmail watcher is healthy."""
        # This is a placeholder - in production, this would:
        # 1. Check if the process is running
        # 2. Verify it's responding to health checks
        # For now, return True
        return True

    # Add GmailWatcher configuration
    configs.append(ComponentConfig(
        name="GmailWatcher",
        start_command=start_gmail_watcher,
        health_check=check_gmail_watcher_health,
        restart_on_failure=True,
        max_restart_attempts=3,
        restart_backoff_seconds=60,
        crash_detection_window_minutes=5,
        crash_threshold=3
    ))

    # Add more component configurations here as needed
    # Example: FileProcessor, LinkedInPoster, etc.

    return configs


def main():
    """Main entry point for watchdog process."""
    parser = argparse.ArgumentParser(
        description="Start the AI Employee watchdog process"
    )
    parser.add_argument(
        "--vault-path",
        type=Path,
        default=Path.home() / "AI_Employee_Vault",
        help="Path to AI_Employee_Vault (default: ~/AI_Employee_Vault)"
    )
    parser.add_argument(
        "--check-interval",
        type=int,
        default=30,
        help="Health check interval in seconds (default: 30)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("Starting AI Employee Watchdog")
    logger.info("=" * 60)
    logger.info(f"Vault path: {args.vault_path}")
    logger.info(f"Check interval: {args.check_interval}s")
    logger.info(f"Log level: {args.log_level}")

    # Verify vault path exists
    if not args.vault_path.exists():
        logger.error(f"Vault path does not exist: {args.vault_path}")
        logger.error("Please create the vault directory or specify correct path with --vault-path")
        sys.exit(1)

    # Initialize error logger
    logs_dir = args.vault_path / "Logs" / "Errors"
    dashboard_path = args.vault_path / ".system" / "error_dashboard.json"
    error_logger = ErrorLogger(logs_dir, dashboard_path)

    # Initialize watchdog
    watchdog = Watchdog(
        vault_path=args.vault_path,
        check_interval_seconds=args.check_interval,
        error_logger=error_logger
    )

    # Register components
    logger.info("Registering components...")
    component_configs = create_component_configs(args.vault_path)

    if not component_configs:
        logger.warning("No components configured for monitoring")
        logger.warning("Edit start_watchdog.py to add component configurations")

    for config in component_configs:
        watchdog.register_component(config)
        logger.info(f"  - {config.name}")

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        watchdog.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start watchdog
    logger.info("Starting watchdog monitoring loop...")
    logger.info("Press Ctrl+C to stop")

    try:
        watchdog.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
        watchdog.stop()
    except Exception as e:
        logger.error(f"Watchdog crashed: {e}", exc_info=True)
        sys.exit(1)

    logger.info("Watchdog stopped")


if __name__ == "__main__":
    main()
