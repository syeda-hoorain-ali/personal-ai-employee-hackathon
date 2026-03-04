#!/usr/bin/env python3
"""
Standalone Environment Variable Sync Script
Run this script after updating your .env file to sync changes to system environment variables.

Usage:
    python scripts/sync_env_vars.py

Requirements:
    - None (uses only Python standard library)
    - .env file must exist in project root
"""

import sys
from pathlib import Path

# Add scripts directory to path for importing env_sync
sys.path.insert(0, str(Path(__file__).parent))

try:
    import env_sync
except ImportError as e:
    print(f"[ERROR] Failed to import env_sync module: {e}")
    print("        Make sure env_sync.py exists in the scripts/ directory")
    sys.exit(1)


def main():
    """Main function to sync environment variables."""
    print("=" * 60)
    print("Personal AI Employee - Environment Variable Sync")
    print("=" * 60)
    print()

    # Determine .env file path (project root)
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"

    if not env_file.exists():
        print(f"[ERROR] .env file not found at: {env_file}")
        print()
        print("Please create a .env file by copying .env.example:")
        print(f"    cp .env.example .env")
        print()
        print("Then fill in your configuration values and run this script again.")
        return 1

    print(f"[INFO] Using .env file: {env_file}")
    print()

    # Sync environment variables
    success = env_sync.sync_env_variables(env_path=str(env_file), verbose=True)

    print()
    if success:
        print("=" * 60)
        print("[SUCCESS] Environment variables synced successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("  • Variables are now available in this terminal session")
        if env_sync.is_windows():
            print("  • New terminals will automatically have these variables")
            print("  • MCP servers will use these variables when started")
        else:
            print("  • Run 'source ~/.bashrc' to load in current terminal")
            print("  • New terminals will automatically have these variables")
        print()
        return 0
    else:
        print("=" * 60)
        print("[WARNING] Some variables had issues (see output above)")
        print("=" * 60)
        print()
        print("Variables are still available in current session.")
        print("Check the warnings above for details.")
        print()
        return 0  # Don't fail completely, session vars are still set


if __name__ == '__main__':
    sys.exit(main())