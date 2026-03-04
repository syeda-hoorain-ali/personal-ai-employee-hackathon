#!/usr/bin/env python3
"""
Setup script for the Personal AI Employee system.
This script performs all initial setup tasks.
"""

import json
import os
import sys
import subprocess
from pathlib import Path

# Import env_sync module for environment variable synchronization
sys.path.insert(0, str(Path(__file__).parent))
import env_sync

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


def setup_weekly_audit_scheduler():
    """
    Set up a scheduled task to run the weekly CEO briefing every Monday at 8:00 AM.
    Only runs if the script is executed with administrator privileges.
    """
    # Check if running as administrator
    if not is_admin():
        print("[WARNING] Weekly briefing scheduler setup requires administrator privileges.")
        print("         Skipping weekly briefing scheduler setup.")
        print("         Please run this script as an administrator to enable automatic weekly briefings.")
        return False

    print("[INFO] Setting up Weekly CEO Briefing scheduler...")

    # Check OS type
    if os.name != 'nt':  # Not Windows
        print(f"[INFO] For Unix/Linux systems, use cron to schedule weekly briefings.")
        print("         Add this to your crontab (crontab -e):")
        print(f"         0 8 * * 1 cd /path/to/project && python app/scripts/weekly_briefing_trigger.py")
        return False

    task_name = "WeeklyCEOBriefing"
    project_root = Path(__file__).parent.parent.resolve()
    python_exe = sys.executable
    trigger_script = project_root / "app" / "scripts" / "weekly_briefing_trigger.py"

    # Verify trigger script exists
    if not trigger_script.exists():
        print(f"[ERROR] Trigger script not found at: {trigger_script}")
        return False

    # First, try to delete the existing task if it exists
    delete_cmd = ['schtasks', '/delete', '/tn', task_name, '/f']
    try:
        subprocess.run(delete_cmd, capture_output=True, text=True, check=False)
        print(f"[INFO] Deleted existing task '{task_name}' if it existed")
    except Exception as e:
        print(f"[INFO] No existing task to delete or error deleting: {e}")

    # Create the scheduled task using schtasks (simpler than PowerShell)
    create_cmd = [
        'schtasks', '/create',
        '/tn', task_name,
        '/tr', f'"{python_exe}" "{trigger_script}"',
        '/sc', 'weekly',
        '/d', 'MON',
        '/st', '08:00',
        '/rl', 'HIGHEST',
        '/f'
    ]

    try:
        result = subprocess.run(
            create_cmd,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"[SUCCESS] Successfully created scheduled task '{task_name}'")
        print(f"[SUCCESS] The task will run weekly CEO briefing every Monday at 8:00 AM")
        print(f"[INFO] Architecture: Trigger → Claude Code → Skills + Odoo MCP")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error creating scheduled task: {e}")
        print(f"[ERROR] Error output: {e.stderr}")
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

    # Sync environment variables from .env file
    print("0. Syncing environment variables from .env file...")
    env_file = Path(".env")

    if not env_file.exists():
        print("[WARNING] .env file not found!")
        print("          Please create a .env file by copying .env.example:")
        print("          cp .env.example .env")
        print()
        print("          Then fill in your configuration values.")
        print("          Continuing setup without environment variables...")
        print()
    else:
        # Sync environment variables
        env_sync.sync_env_variables(env_path=str(env_file), verbose=True)
        print()

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
            "AI_Employee_Vault/Accounting",
            "AI_Employee_Vault/Briefings"
        ]

        for dir_path in vault_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            print(f"[SUCCESS] Created directory: {dir_path}")

    print()
    print("4. Checking for Gmail credentials...")

    credentials_path = Path.home() / ".gmail-mcp" / "gcp-oauth.keys.json"
    if not credentials_path.exists():
        print("[WARNING] Gmail credentials file not found at ~/.gmail-mcp/gcp-oauth.keys.json")
        print("   To enable Gmail monitoring, you need to:")
        print("   1. Create a Google Cloud project")
        print("   2. Enable Gmail API")
        print("   3. Download credentials as 'gcp-oauth.keys.json'")
        print("   4. Place it in ~/.gmail-mcp/ directory")
        print()
        # Automatically continue without Gmail monitoring in non-interactive mode
        print("Continuing without Gmail monitoring...")
        # response = input()
        response = 'y'
        if response.lower() not in ['y', 'yes']:
            print("[ERROR] Setup cancelled. Please follow the instructions above to set up Gmail credentials.")
            return 1
    else:
        print("[SUCCESS] Gmail credentials found at ~/.gmail-mcp/gcp-oauth.keys.json")

        # Try to authenticate
        print("[INFO] Authenticating with Gmail...")
        try:
            # Try to load existing token
            token_path = Path.home() / ".gmail-mcp" / "credentials.json"
            creds = None

            if token_path.exists():
                with open(token_path, 'r') as token:
                    token_data = json.load(token)

                # Create credentials object from token data
                from google.oauth2.credentials import Credentials
                creds = Credentials(
                    token=token_data.get('access_token'),
                    refresh_token=token_data.get('refresh_token'),
                    id_token=token_data.get('id_token'),
                    token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
                    client_id=token_data.get('client_id'),
                    client_secret=token_data.get('client_secret'),
                    scopes=token_data.get('scopes', ['https://www.googleapis.com/auth/gmail.readonly'])
                )

            # If there are no valid credentials, get new ones using the npx command
            if not creds or not creds.valid:
                print("   Running npx command to authenticate and create credentials...")
                print("   A browser window will open for authentication.")
                print("   Please complete the authentication process.")

                try:
                    result = subprocess.run([
                        "npx", "-y", "@gongrzhe/server-gmail-autoauth-mcp", "auth"
                    ], shell=True, capture_output=True, text=True)

                    if result.returncode != 0:
                        print("   Gmail authentication failed.")
                        print(f"   Error: {result.stderr}")
                        print("   Try running command manually: 'npx -y @gongrzhe/server-gmail-autoauth-mcp auth'")
                    else:
                        print("   Gmail authentication completed successfully")

                        # Reload the credentials after the npx command creates them
                        if token_path.exists():
                            with open(token_path, 'r') as token:
                                token_data = json.load(token)

                            from google.oauth2.credentials import Credentials
                            creds = Credentials(
                                token=token_data.get('access_token'),
                                refresh_token=token_data.get('refresh_token'),
                                id_token=token_data.get('id_token'),
                                token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
                                client_id=token_data.get('client_id'),
                                client_secret=token_data.get('client_secret'),
                                scopes=token_data.get('scopes', ['https://www.googleapis.com/auth/gmail.readonly'])
                            )
                except Exception as e:
                    print(f"   Error running npx command: {e}")
                    print("   Gmail authentication failed.")

                print("[SUCCESS] Gmail authentication completed successfully")
            else:
                print("[SUCCESS] Gmail credentials are valid")

            # Register MCP servers after successful Gmail authentication
            print("[INFO] Registering MCP servers...")
            try:
                # Run MCP server registration commands
                mcp_commands = [
                    ["claude", "mcp", "add", "--scope", "project", "--transport", "stdio", "gmail", "--", "npx", "-y", "@gongrzhe/server-gmail-autoauth-mcp"],
                    ["claude", "mcp", "add", "--scope", "project", "--transport", "stdio", "context7", "--", "npx", "-y", "@upstash/context7-mcp"],
                    ["claude", "mcp", "add", "--scope", "project", "--transport", "stdio", "playwright", "--", "npx", "-y", "@playwright/mcp@latest"],
                    # ["claude", "mcp", "add", "--scope", "project", "--transport", "stdio", "xero", "--env", "XERO_CLIENT_ID='${XERO_CLIENT_ID}'", "--env", "XERO_CLIENT_SECRET='${XERO_CLIENT_SECRET}'", "--", "npx", "-y", "@xeroapi/xero-mcp-server@latest"],
                    ["claude", "mcp", "add", "--scope", "project", "--transport", "stdio", "twitter-x", "--env", "AUTH_TYPE='oauth2", "--env", "OAUTH2_CLIENT_ID='${X_CLIENT_ID}'", "--env", "OAUTH2_CLIENT_SECRET='${X_CLIENT_SECRET}'", "--env", "OAUTH2_ACCESS_TOKEN='${X_ACCESS_TOKEN}'", "--env", "OAUTH2_REFRESH_TOKEN='${X_REFRESH_TOKEN}'", "--", "npx", "-y", "@xeroapi/xero-mcp-server@latest"],
                    ["claude", "mcp", "add", "--scope", "project", "--transport", "stdio", "odoo", "--env", "ODOO_URL='${ODOO_URL}'", "--env", "ODOO_USER='${ODOO_USER}'", "--env", "ODOO_API_KEY='${ODOO_API_KEY}'", "--env", "ODOO_DB='${ODOO_DB}'", "--env", "ODOO_YOLO='${ODOO_YOLO}'", "--", "uvx", "mcp-server-odoo"],
                ]

                for cmd in mcp_commands:
                    print(f"[INFO] Running: {' '.join(cmd)}")
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"[SUCCESS] MCP server registered: {cmd[7]}")
                    else:
                        print(f"[ERROR] Failed to register MCP server {cmd[7]}: {result.stderr}")

            except Exception as e:
                print(f"[WARNING] Error registering MCP servers: {e}")

            # Register Ralph Loop plugin
            print("[INFO] Adding Claude plugin marketplace...")
            try:
                # First, add the official Claude plugins marketplace
                marketplace_cmd = ["claude", "plugin", "marketplace", "add", "anthropics/claude-plugins-official"]
                result = subprocess.run(marketplace_cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"[SUCCESS] Claude plugin marketplace added")
                    print(result.stdout)
                else:
                    print(f"[WARNING] Failed to add marketplace (may already exist): {result.stderr}")

                # Then install the Ralph Loop plugin from the marketplace
                print("[INFO] Installing Ralph Loop plugin from marketplace...")
                plugin_cmd = ["claude", "plugin", "install", "--scope", "project", "ralph-loop@claude-plugins-official"]
                result = subprocess.run(plugin_cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"[SUCCESS] Ralph Loop plugin installed")
                    print(result.stdout)
                else:
                    print(f"[ERROR] Failed to install plugin: {result.stderr}")

            except Exception as e:
                print(f"[WARNING] Error with plugin setup: {e}")

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

    try:
        from app.weekly_audit.audit_orchestrator import AuditOrchestrator
        from app.weekly_audit.business_goals_parser import BusinessGoalsParser
        print("[SUCCESS] Weekly CEO Briefing components available")
    except ImportError as e:
        print(f"[WARNING] Weekly CEO Briefing components not available: {e}")
        print("         This feature may not work correctly")

    print()
    print("[5] Setting up Business Goals for Weekly CEO Briefing...")
    # Check if Business_Goals.md exists in vault
    business_goals_path = Path("AI_Employee_Vault/Business_Goals.md")
    if not business_goals_path.exists():
        print("[WARNING] Business_Goals.md not found in AI_Employee_Vault")
        print("         Creating default Business_Goals.md template...")

        # Create default Business_Goals.md
        default_business_goals = """---
revenue_target: 10000.00
current_revenue: 0.00
key_metrics:
  - name: "Client response time"
    target: "< 24 hours"
    alert_threshold: "> 48 hours"
  - name: "Invoice payment rate"
    target: "> 90%"
    alert_threshold: "< 80%"
active_projects:
  - name: "Example Project"
    deadline: "2026-12-31"
    budget: 5000
subscription_rules:
  inactivity_days: 30
  cost_increase_threshold: 0.20
last_updated: "2026-02-19"
review_frequency: "weekly"
---

# Business Goals

Update this file with your actual business metrics and targets.
See the Weekly CEO Briefing documentation for details.
"""
        business_goals_path.write_text(default_business_goals, encoding='utf-8')
        print("[SUCCESS] Created Business_Goals.md template")
        print("         Please update AI_Employee_Vault/Business_Goals.md with your actual business data")
    else:
        print("[SUCCESS] Business_Goals.md found in vault")

    print()
    print("[6] Setting up LinkedIn scheduler...")
    # Set up LinkedIn auto-poster scheduler
    setup_linkedin_scheduler()

    print()
    print("[7] Setting up Weekly CEO Briefing scheduler...")
    # Set up weekly audit scheduler
    setup_weekly_audit_scheduler()

    print()
    print("[SUCCESS] Setup completed successfully!")
    print()
    print("[INFO] Next steps:")
    print("   1. Review the AI_Employee_Vault/Company_Handbook.md for processing rules")
    print("   2. Update AI_Employee_Vault/Business_Goals.md with your business targets")
    print("   3. Place .md files in AI_Employee_Vault/Needs_Action/ to test file processing")
    print("   4. Weekly CEO Briefings will be generated every Sunday at 8:00 PM")
    print("   5. The system will now start automatically")
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
    credentials_path = Path.home() / ".gmail-mcp" / "credentials.json"

    if credentials_path.exists():
        try:
            from app.watchers.gmail_watcher import GmailWatcher

            # Initialize Gmail watcher with the token path (will handle JSON loading)
            gmail_watcher = GmailWatcher(vault_path, str(credentials_path))
            orchestrator.add_watcher(gmail_watcher)
            print("[SUCCESS] Gmail watcher added and configured")
        except Exception as e:
            print(f"[WARNING] Gmail watcher initialization failed: {e}")
            print("   Continuing with file system watcher only")
    else:
        print("[INFO] Gmail credentials not found - starting with file system watcher only")
        print("   To enable Gmail monitoring: place gcp-oauth.keys.json in ~/.gmail-mcp/ and run: 'npx -y @gongrzhe/server-gmail-autoauth-mcp auth'")

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
        if credentials_path.exists():
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
