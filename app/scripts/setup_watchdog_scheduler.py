#!/usr/bin/env python3
"""
Setup script for configuring the watchdog to run automatically on system startup.

This script configures the operating system's task scheduler to start the watchdog
process automatically when the system boots.

Supports:
- Windows: Task Scheduler
- Linux: systemd service
- macOS: launchd
"""

import sys
import platform
import subprocess
import argparse
import logging
from pathlib import Path


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def setup_windows_task_scheduler(
    vault_path: Path,
    python_path: Path,
    script_path: Path,
    check_interval: int
) -> bool:
    """
    Setup Windows Task Scheduler to run watchdog on startup.

    Args:
        vault_path: Path to AI_Employee_Vault
        python_path: Path to Python interpreter
        script_path: Path to start_watchdog.py
        check_interval: Health check interval in seconds

    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)

    task_name = "AIEmployeeWatchdog"

    # Build the command to run
    command = f'"{python_path}" "{script_path}" --vault-path "{vault_path}" --check-interval {check_interval}'

    # XML configuration for the scheduled task
    xml_config = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>AI Employee Watchdog - Monitors and restarts crashed components</Description>
    <Author>AI Employee System</Author>
  </RegistrationInfo>
  <Triggers>
    <BootTrigger>
      <Enabled>true</Enabled>
    </BootTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>
    <IdleSettings>
      <StopOnIdleEnd>false</StopOnIdleEnd>
      <RestartOnIdle>false</RestartOnIdle>
    </IdleSettings>
    <AllowStartOnDemand>true</AllowStartOnDemand>
    <Enabled>true</Enabled>
    <Hidden>false</Hidden>
    <RunOnlyIfIdle>false</RunOnlyIfIdle>
    <WakeToRun>false</WakeToRun>
    <ExecutionTimeLimit>PT0S</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{python_path}</Command>
      <Arguments>"{script_path}" --vault-path "{vault_path}" --check-interval {check_interval}</Arguments>
      <WorkingDirectory>{script_path.parent}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""

    # Save XML to temp file
    xml_file = Path.home() / "watchdog_task.xml"
    try:
        xml_file.write_text(xml_config, encoding='utf-16')

        # Delete existing task if it exists
        logger.info(f"Checking for existing task '{task_name}'...")
        subprocess.run(
            ["schtasks", "/Delete", "/TN", task_name, "/F"],
            capture_output=True,
            check=False  # Don't fail if task doesn't exist
        )

        # Create the scheduled task
        logger.info(f"Creating scheduled task '{task_name}'...")
        result = subprocess.run(
            ["schtasks", "/Create", "/TN", task_name, "/XML", str(xml_file)],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            logger.info("✓ Scheduled task created successfully")
            logger.info(f"  Task name: {task_name}")
            logger.info(f"  Trigger: On system startup")
            logger.info(f"  Command: {command}")
            logger.info("")
            logger.info("To manage the task:")
            logger.info(f"  - View: schtasks /Query /TN {task_name} /V /FO LIST")
            logger.info(f"  - Run now: schtasks /Run /TN {task_name}")
            logger.info(f"  - Stop: schtasks /End /TN {task_name}")
            logger.info(f"  - Delete: schtasks /Delete /TN {task_name} /F")
            return True
        else:
            logger.error(f"Failed to create scheduled task: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Error setting up Windows Task Scheduler: {e}")
        return False
    finally:
        # Clean up temp XML file
        if xml_file.exists():
            xml_file.unlink()


def setup_linux_systemd(
    vault_path: Path,
    python_path: Path,
    script_path: Path,
    check_interval: int
) -> bool:
    """
    Setup systemd service to run watchdog on startup (Linux).

    Args:
        vault_path: Path to AI_Employee_Vault
        python_path: Path to Python interpreter
        script_path: Path to start_watchdog.py
        check_interval: Health check interval in seconds

    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)

    service_name = "ai-employee-watchdog"
    service_file = Path(f"/etc/systemd/system/{service_name}.service")

    # systemd service configuration
    service_config = f"""[Unit]
Description=AI Employee Watchdog
After=network.target

[Service]
Type=simple
User={Path.home().owner()}
ExecStart={python_path} {script_path} --vault-path {vault_path} --check-interval {check_interval}
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

    logger.info("Creating systemd service configuration...")
    logger.info(f"Service file: {service_file}")
    logger.info("")
    logger.info("Please run the following commands as root:")
    logger.info("")
    logger.info(f"# Create service file")
    logger.info(f"sudo tee {service_file} > /dev/null << 'EOF'")
    logger.info(service_config)
    logger.info("EOF")
    logger.info("")
    logger.info("# Reload systemd and enable service")
    logger.info("sudo systemctl daemon-reload")
    logger.info(f"sudo systemctl enable {service_name}")
    logger.info(f"sudo systemctl start {service_name}")
    logger.info("")
    logger.info("# Check status")
    logger.info(f"sudo systemctl status {service_name}")

    return True


def setup_macos_launchd(
    vault_path: Path,
    python_path: Path,
    script_path: Path,
    check_interval: int
) -> bool:
    """
    Setup launchd to run watchdog on startup (macOS).

    Args:
        vault_path: Path to AI_Employee_Vault
        python_path: Path to Python interpreter
        script_path: Path to start_watchdog.py
        check_interval: Health check interval in seconds

    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)

    plist_name = "com.aiemployee.watchdog"
    plist_file = Path.home() / "Library" / "LaunchAgents" / f"{plist_name}.plist"

    # launchd plist configuration
    plist_config = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{plist_name}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>{script_path}</string>
        <string>--vault-path</string>
        <string>{vault_path}</string>
        <string>--check-interval</string>
        <string>{check_interval}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{Path.home()}/Library/Logs/ai-employee-watchdog.log</string>
    <key>StandardErrorPath</key>
    <string>{Path.home()}/Library/Logs/ai-employee-watchdog-error.log</string>
</dict>
</plist>
"""

    try:
        # Create LaunchAgents directory if it doesn't exist
        plist_file.parent.mkdir(parents=True, exist_ok=True)

        # Write plist file
        logger.info(f"Creating launchd configuration: {plist_file}")
        plist_file.write_text(plist_config)

        # Load the launch agent
        logger.info("Loading launch agent...")
        result = subprocess.run(
            ["launchctl", "load", str(plist_file)],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            logger.info("✓ Launch agent loaded successfully")
            logger.info(f"  Label: {plist_name}")
            logger.info(f"  Plist: {plist_file}")
            logger.info("")
            logger.info("To manage the service:")
            logger.info(f"  - Stop: launchctl unload {plist_file}")
            logger.info(f"  - Start: launchctl load {plist_file}")
            logger.info(f"  - View logs: tail -f ~/Library/Logs/ai-employee-watchdog.log")
            return True
        else:
            logger.error(f"Failed to load launch agent: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Error setting up launchd: {e}")
        return False


def main():
    """Main entry point for scheduler setup."""
    parser = argparse.ArgumentParser(
        description="Setup AI Employee watchdog to run automatically on system startup"
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
        "--python-path",
        type=Path,
        default=Path(sys.executable),
        help="Path to Python interpreter (default: current Python)"
    )

    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("AI Employee Watchdog Scheduler Setup")
    logger.info("=" * 60)

    # Determine script path
    script_path = Path(__file__).parent / "start_watchdog.py"
    if not script_path.exists():
        logger.error(f"start_watchdog.py not found at: {script_path}")
        sys.exit(1)

    logger.info(f"Platform: {platform.system()}")
    logger.info(f"Python: {args.python_path}")
    logger.info(f"Script: {script_path}")
    logger.info(f"Vault: {args.vault_path}")
    logger.info(f"Check interval: {args.check_interval}s")
    logger.info("")

    # Verify vault path exists
    if not args.vault_path.exists():
        logger.error(f"Vault path does not exist: {args.vault_path}")
        logger.error("Please create the vault directory or specify correct path with --vault-path")
        sys.exit(1)

    # Setup based on platform
    system = platform.system()

    if system == "Windows":
        success = setup_windows_task_scheduler(
            args.vault_path,
            args.python_path,
            script_path,
            args.check_interval
        )
    elif system == "Linux":
        success = setup_linux_systemd(
            args.vault_path,
            args.python_path,
            script_path,
            args.check_interval
        )
    elif system == "Darwin":  # macOS
        success = setup_macos_launchd(
            args.vault_path,
            args.python_path,
            script_path,
            args.check_interval
        )
    else:
        logger.error(f"Unsupported platform: {system}")
        logger.error("Supported platforms: Windows, Linux, macOS")
        sys.exit(1)

    if success:
        logger.info("")
        logger.info("=" * 60)
        logger.info("✓ Setup completed successfully!")
        logger.info("=" * 60)
        logger.info("The watchdog will now start automatically on system boot.")
    else:
        logger.error("")
        logger.error("=" * 60)
        logger.error("✗ Setup failed")
        logger.error("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
