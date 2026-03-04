#!/usr/bin/env python3
"""
Environment Variable Sync Module
Syncs environment variables from .env file to system (permanent) and session (temporary).
Uses only Python standard library - no external dependencies required.
"""

import os
import sys
import subprocess
import re
from pathlib import Path


def is_windows():
    """Check if running on Windows."""
    return sys.platform.startswith('win')


def parse_env_file(env_path):
    """
    Parse .env file and return dictionary of environment variables.
    Handles comments, empty lines, quoted values, and unquoted values.

    Args:
        env_path: Path to .env file

    Returns:
        dict: Dictionary of environment variable key-value pairs
    """
    env_vars = {}

    if not Path(env_path).exists():
        print(f"[WARNING] .env file not found at: {env_path}")
        return env_vars

    # Pattern to match KEY=value or KEY="value" or KEY='value'
    pattern = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$')

    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue

                match = pattern.match(line)
                if match:
                    key = match.group(1)
                    value = match.group(2).strip()

                    # Remove surrounding quotes if present
                    if len(value) >= 2:
                        if (value.startswith('"') and value.endswith('"')) or \
                           (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]

                    env_vars[key] = value
                else:
                    # Line doesn't match expected format
                    if '=' in line:
                        print(f"[WARNING] Line {line_num} has unexpected format: {line}")

        return env_vars

    except Exception as e:
        print(f"[ERROR] Failed to parse .env file: {e}")
        return {}


def set_permanent_env_var_windows(key, value):
    """
    Set environment variable permanently on Windows using setx.

    Args:
        key: Environment variable name
        value: Environment variable value

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Use setx to set user-level environment variable
        result = subprocess.run(
            ['setx', key, value],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            return True
        else:
            print(f"[WARNING] Failed to set {key} permanently: {result.stderr.strip()}")
            return False

    except Exception as e:
        print(f"[WARNING] Failed to set {key} permanently: {e}")
        return False


def set_permanent_env_var_unix(key, value):
    """
    Set environment variable permanently on Unix by appending to shell profile.

    Args:
        key: Environment variable name
        value: Environment variable value

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        home = Path.home()

        # Detect which shell profile to use
        shell_profiles = [
            home / '.bashrc',
            home / '.bash_profile',
            home / '.zshrc',
            home / '.profile'
        ]

        # Find the first existing profile, or default to .bashrc
        profile = None
        for p in shell_profiles:
            if p.exists():
                profile = p
                break

        if profile is None:
            profile = home / '.bashrc'
            print(f"[INFO] Creating new shell profile: {profile}")

        # Check if variable already exists in profile
        export_line = f'export {key}="{value}"'

        if profile.exists():
            with open(profile, 'r', encoding='utf-8') as f:
                content = f.read()
                # Check if this exact export already exists
                if export_line in content:
                    return True
                # Check if variable is set with different value
                if re.search(rf'^export\s+{re.escape(key)}=', content, re.MULTILINE):
                    print(f"[INFO] Variable {key} already exists in {profile}, skipping")
                    return True

        # Append export statement to profile
        with open(profile, 'a', encoding='utf-8') as f:
            f.write(f'\n# Added by Personal AI Employee setup\n')
            f.write(f'{export_line}\n')

        print(f"[INFO] Added {key} to {profile}")
        return True

    except Exception as e:
        print(f"[WARNING] Failed to set {key} permanently: {e}")
        return False


def set_session_env_var(key, value):
    """
    Set environment variable in current session.

    Args:
        key: Environment variable name
        value: Environment variable value
    """
    os.environ[key] = value


def sync_env_variables(env_path='.env', verbose=True):
    """
    Main function to sync environment variables from .env file.
    Sets variables both permanently (system-level) and in current session.

    Args:
        env_path: Path to .env file (default: '.env')
        verbose: Print detailed output (default: True)

    Returns:
        bool: True if successful, False if errors occurred
    """
    if verbose:
        print("[INFO] Syncing environment variables from .env file...")

    # Parse .env file
    env_vars = parse_env_file(env_path)

    if not env_vars:
        print("[WARNING] No environment variables found in .env file")
        return False

    if verbose:
        print(f"[INFO] Found {len(env_vars)} environment variables")

    # Track success/failure
    success_count = 0
    failure_count = 0

    # Set each variable
    for key, value in env_vars.items():
        if verbose:
            # Mask sensitive values in output
            display_value = value
            if any(sensitive in key.upper() for sensitive in ['PASSWORD', 'SECRET', 'KEY', 'TOKEN']):
                display_value = '***' if not value else ('*' * min(len(value), 8))
            print(f"[INFO] Setting {key}={display_value}")

        # Set permanently based on platform
        if is_windows():
            permanent_success = set_permanent_env_var_windows(key, value)
        else:
            permanent_success = set_permanent_env_var_unix(key, value)

        # Set in current session
        set_session_env_var(key, value)

        if permanent_success:
            success_count += 1
        else:
            failure_count += 1

    # Summary
    if verbose:
        print()
        print(f"[SUCCESS] Environment variables synced:")
        print(f"          {success_count} variables set successfully")
        if failure_count > 0:
            print(f"          {failure_count} variables had warnings (check output above)")
        print(f"          Variables are available in current session")

        if is_windows():
            print(f"          Permanent variables set via setx (user-level)")
            print(f"          Note: New terminals will have these variables")
        else:
            print(f"          Permanent variables added to shell profile")
            print(f"          Note: Run 'source ~/.bashrc' or restart terminal to load")

    return failure_count == 0


if __name__ == '__main__':
    # Allow running this module directly for testing
    success = sync_env_variables()
    sys.exit(0 if success else 1)
