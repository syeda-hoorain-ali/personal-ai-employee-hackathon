#!/usr/bin/env python3
"""
Setup script for the Personal AI Employee system.
This script performs all initial setup tasks.
"""

import os
import sys
import subprocess
from pathlib import Path

def is_admin():
    """Check if the script is running with administrator privileges."""
    try:
        # For Windows
        if os.name == 'nt':
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        # For Unix-like systems
        else:
            return os.geteuid() == 0
    except AttributeError:
        # If we can't determine, assume not an admin (safer assumption)
        return False


def run_command(cmd, desc):
    """Run a command and show status."""
    print(f"[INFO] {desc}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[SUCCESS] {desc} completed successfully")
            return True
        else:
            print(f"[ERROR] {desc} failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"[ERROR] {desc} failed with exception: {e}")
        return False


def setup_linkedin_scheduler():
    """
    Set up a scheduled task to run the LinkedIn poster script periodically.
    Only runs if the script is executed with administrator privileges.
    """
    # Check if running as administrator
    if not is_admin():
        print("[WARNING] LinkedIn scheduler setup requires administrator privileges.")
        print("         Skipping LinkedIn scheduler setup.")
        print("         Please run this script as an administrator to enable automatic LinkedIn posting.")
        return False

    print("[INFO] Setting up LinkedIn auto-poster scheduler...")

    # Check OS type
    if os.name != 'nt':  # Not Windows
        print(f"[WARNING] Task Scheduler is not available on this OS ({sys.platform}).")
        print("         Skipping LinkedIn scheduler setup.")
        return False

    task_name = "LinkedInAutoPoster"
    script_path = Path("app/scripts/linkedin_poster_cli.py").resolve()

    # Verify the script exists
    if not script_path.exists():
        print(f"[ERROR] LinkedIn poster script {script_path} does not exist!")
        return False

    app_folder = script_path.parent.parent.resolve()
    python_exe = sys.executable

    # First, try to delete the existing task if it exists
    delete_cmd = ['schtasks', '/delete', '/tn', task_name, '/f']
    try:
        subprocess.run(delete_cmd, capture_output=True, text=True, check=False)
        print(f"[INFO] Deleted existing task '{task_name}' if it existed")
    except Exception as e:
        print(f"[INFO] No existing task to delete or error deleting: {e}")

    # PowerShell script to create the task
    ps_script = f'''
    $action = New-ScheduledTaskAction -Execute "{python_exe}" -Argument '"{script_path}"' -WorkingDirectory "{app_folder}"

    # Trigger: Run every day at 12:00 PM (noon) - good for business posting
    $trigger = New-ScheduledTaskTrigger -Daily -At "12:00PM"

    # Settings to ensure task runs reliably
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable:$true `
        -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
        -MultipleInstances Queue

    # Principal to run whether logged in or not
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType ServiceAccount -RunLevel Highest

    # Register the task
    Register-ScheduledTask -TaskName "{task_name}" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force
    '''

    try:
        # Create new task using PowerShell
        result = subprocess.run(
            ['powershell', '-Command', ps_script],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"[SUCCESS] Successfully created scheduled task '{task_name}'")
        print(f"[SUCCESS] The task will run '{script_path}' daily at 12:00 PM")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error creating scheduled task: {e}")
        print(f"[ERROR] Error output: {e.stderr}")
        return False

def main():
    """Main setup function."""
    print("Personal AI Employee - Setup Script")
    print("=" * 50)
    print("This script will set up the complete system.")
    print()

    # Check if we're in the root directory (where app/ subdirectory exists)
    if not Path("app").exists():
        print("ERROR: Please run this script from the project root directory")
        return 1

    print("1. Setting up virtual environment...")
    # Check if virtual environment already exists
    venv_path = Path("app/.venv")
    if venv_path.exists():
        print("Virtual environment already exists, skipping creation...")
        print("[SUCCESS] Using existing virtual environment")
    else:
        if not run_command("cd app && uv venv", "Creating virtual environment with uv"):
            print("ERROR: Virtual environment creation failed. Please install uv and try again.")
            return 1

    print("2. Installing dependencies...")
    if not run_command("cd app && uv sync", "Installing dependencies with uv"):
        print("ERROR: Dependency installation failed. Please install uv and try again.")
        return 1

    print()
    print("3. Setting up vault structure...")
    # Create vault structure using the setup script
    vault_setup_script = Path("app/scripts/setup_vault.py")
    if vault_setup_script.exists():
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("setup_vault", vault_setup_script)
            if spec is None:
                print(f"[ERROR] Could not load spec from {vault_setup_script}")
                return 1
            setup_vault_module = importlib.util.module_from_spec(spec)
            if spec.loader is None:
                print(f"[ERROR] Spec loader is None for {vault_setup_script}")
                return 1
            spec.loader.exec_module(setup_vault_module)

            # Call the main setup function directly with force=True to avoid interactive prompts
            import sys
            original_argv = sys.argv
            sys.argv = ["setup_vault", "--force"]  # Pass --force to avoid prompts
            try:
                setup_vault_module.main()
            finally:
                sys.argv = original_argv  # Restore original argv
            print("[SUCCESS] Vault structure created successfully")
        except Exception as e:
            print(f"[ERROR] Vault setup failed: {e}")
            return 1
    else:
        print("[ERROR] Setup script not found, creating vault structure manually...")
        vault_dirs = [
            "AI_Employee_Vault/Inbox",
            "AI_Employee_Vault/Needs_Action",
            "AI_Employee_Vault/Done",
            "AI_Employee_Vault/Plans",
            "AI_Employee_Vault/Pending_Approval",
            "AI_Employee_Vault/Approved",
            "AI_Employee_Vault/Rejected",
            "AI_Employee_Vault/Logs",
            "AI_Employee_Vault/Accounting"
        ]

        for dir_path in vault_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            print(f"[SUCCESS] Created directory: {dir_path}")

    print()
    print("4. Checking for Gmail credentials...")

    credentials_path = Path("gmail_credentials.json")
    if not credentials_path.exists():
        print("[WARNING] Gmail credentials file not found.")
        print("   To enable Gmail monitoring, you need to:")
        print("   1. Create a Google Cloud project")
        print("   2. Enable Gmail API")
        print("   3. Download credentials as 'gmail_credentials.json'")
        print("   4. Place it in the main project directory")
        print()
        # Automatically continue without Gmail monitoring in non-interactive mode
        print("Continuing without Gmail monitoring...")
        # response = input()
        response = 'y'
        if response.lower() not in ['y', 'yes']:
            print("[ERROR] Setup cancelled. Please follow the instructions above to set up Gmail credentials.")
            return 1
    else:
        print("[SUCCESS] Gmail credentials found")

        # Try to authenticate
        print("[INFO] Authenticating with Gmail...")
        try:
            from google.auth.transport.requests import Request
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.exceptions import RefreshError
            import pickle

            SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

            # Try to load existing token
            token_path = Path("token.pickle")
            creds = None

            if token_path.exists() :
                with open(token_path, 'rb') as token:
                    creds = pickle.load(token)

            # If there are no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                    except RefreshError:
                        # Need to re-authenticate
                        print("   Need to re-authenticate with Google...")
                else:
                    print("   Authenticating with Google for the first time...")
                    print("   A browser window will open for authentication.")
                    print("   Please complete the authentication process.")

                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(credentials_path), SCOPES)
                    creds = flow.run_local_server(port=0)

                # Save credentials for next run
                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)

                print("[SUCCESS] Gmail authentication completed successfully")
            else:
                print("[SUCCESS] Gmail credentials are valid")
        except ImportError:
            print("[WARNING] Google libraries not available, skipping authentication")
            print("   Run 'uv sync' to install Google dependencies")
        except Exception as e:
            print(f"[WARNING] Gmail authentication failed: {e}")
            print("   Gmail monitoring will be disabled")

    print()
    print("[4] Verifying system components...")

    # Test imports
    # Add the app/src directory to the Python path to allow imports
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'src'))

    try:
        from app.file_processor import FileProcessor
        from app.watchers.filesystem_watcher import FileSystemWatcher
        print("[SUCCESS] File system components working")
    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        return 1

    try:
        from app.watchers.gmail_watcher import GmailWatcher
        print("[SUCCESS] Gmail components available")
    except ImportError:
        print("[INFO] Gmail components not available (this is OK if Google libraries weren't installed)")

    print()
    print("[5] Setting up LinkedIn scheduler...")
    # Set up LinkedIn auto-poster scheduler
    setup_linkedin_scheduler()

    print()
    print("[SUCCESS] Setup completed successfully!")
    print()
    print("[INFO] Next steps:")
    print("   1. Review the AI_Employee_Vault/Company_Handbook.md for processing rules")
    print("   2. Place .md files in AI_Employee_Vault/Needs_Action/ to test file processing")
    print("   3. The system will now start automatically")
    print()

    # Automatically start the system after setup
    print("Starting the AI Employee system automatically...")
    print("Place .md files in AI_Employee_Vault/Needs_Action to test file processing")
    print("If Gmail monitoring is enabled, it will monitor your Gmail")
    print("Press Ctrl+C to stop the system")
    print("-" * 50)

    try:
        from app.orchestrator import Orchestrator
        from app.watchers.filesystem_watcher import FileSystemWatcher
        from app.logging_config import setup_logging
    except ImportError as e:
        print(f"[ERROR] Failed to import required modules after setup: {e}")
        print("   The system was set up but cannot start automatically.")
        return 0

    # Setup logging
    setup_logging()
    print("[SUCCESS] Logging initialized")

    # Define vault path
    vault_path = "AI_Employee_Vault"
    print(f"[INFO] Using vault directory: {vault_path}")

    # Create orchestrator
    orchestrator = Orchestrator(vault_path)
    print("[SUCCESS] Orchestrator initialized")

    # Add filesystem watcher
    try:
        fs_watcher = FileSystemWatcher(vault_path)
        orchestrator.add_watcher(fs_watcher)
        print("[SUCCESS] File system watcher added and configured")
    except Exception as e:
        print(f"[ERROR] Failed to initialize file system watcher: {e}")
        return 1

    # Add Gmail watcher if credentials are available
    credentials_path = Path("gmail_credentials.json")
    token_path = Path("token.pickle")

    if credentials_path.exists() and token_path.exists():
        try:
            from app.watchers.gmail_watcher import GmailWatcher
            import pickle

            # Load credentials
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)

            gmail_watcher = GmailWatcher(vault_path, str(token_path))
            orchestrator.add_watcher(gmail_watcher)
            print("[SUCCESS] Gmail watcher added and configured")
        except Exception as e:
            print(f"[WARNING] Gmail watcher initialization failed: {e}")
            print("   Continuing with file system watcher only")
    else:
        print("[INFO] Gmail credentials not found - starting with file system watcher only")
        print("   To enable Gmail monitoring: place gmail_credentials.json and token.pickle in the main directory")

    print("[SUCCESS] All available watchers configured")
    print("\nStarting watchers...")
    print("Place .md files in AI_Employee_Vault/Needs_Action to test file processing")
    print("If Gmail monitoring is enabled, it will monitor your Gmail")
    print("Press Ctrl+C to stop the system")
    print("-" * 50)

    # Start the orchestrator (this will run indefinitely)
    try:
        orchestrator.start_all_watchers()
        print("[SUCCESS] All watchers started successfully")
        print("\nAI Employee is now monitoring for tasks...")
        print("   • File system: Monitoring AI_Employee_Vault/Needs_Action/ for .md files")
        if credentials_path.exists() and token_path.exists():
            print("   • Gmail: Monitoring your Gmail account for important emails")
        print("   • Activity will be logged to the Dashboard.md file")

        # Keep the main thread alive
        import signal
        import time

        def signal_handler(sig, frame):
            print("\n\nReceived interrupt signal")
            print("Stopping watchers...")
            orchestrator.stop_all_watchers()
            print("[SUCCESS] System stopped gracefully")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nReceived interrupt signal")
        print("Stopping watchers...")
        orchestrator.stop_all_watchers()
        print("[SUCCESS] System stopped gracefully")
    except Exception as e:
        print(f"[ERROR] Error running orchestrator: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
