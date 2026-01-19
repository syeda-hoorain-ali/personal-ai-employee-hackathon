#!/usr/bin/env python3
"""
Setup script for the Personal AI Employee system.
This script performs all initial setup tasks.
"""

import os
import sys
import subprocess
from pathlib import Path

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

def main():
    """Main setup function."""
    print("Personal AI Employee - Setup Script")
    print("=" * 50)
    print("This script will set up the complete system.")
    print()

    # Test imports
    # Add the app/src directory to the Python path to allow imports
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'src'))

    try:
        from app.file_processor import FileProcessor
        from app.watchers.filesystem_watcher import FileSystemWatcher
    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        return 1

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

    # Define vault path
    vault_path = "AI_Employee_Vault"

    # Create orchestrator
    orchestrator = Orchestrator(vault_path)

    # Add filesystem watcher
    try:
        fs_watcher = FileSystemWatcher(vault_path)
        orchestrator.add_watcher(fs_watcher)
    except Exception as e:
        print(f"[ERROR] Failed to initialize file system watcher: {e}")
        return 1


    # Start the orchestrator (this will run indefinitely)
    try:
        orchestrator.start_all_watchers()
        print("[SUCCESS] All watchers started successfully")

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
