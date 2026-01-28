#!/usr/bin/env python3
"""
Script to run Claude Code and ask it to post on LinkedIn using the LinkedIn poster skill.
This script is part of the Silver Tier requirements for automated LinkedIn posting.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_linkedin_poster():
    """
    Run Claude Code with the LinkedIn poster skill to create and post content.
    """
    # Define the prompt for Claude Code to use the LinkedIn poster skill
    prompt = (
        "First, use the linkedin-content-writer skill to generate high-quality LinkedIn post content that focuses on business updates to generate sales. "
        "The content should highlight business value, recent achievements, or industry insights that would interest potential customers. "
        "Then, use the playwright tools and linkedin-poster skill to publish the generated content."
    )

    try:
        print("Triggering Claude Code to post on LinkedIn...")

        # Execute Claude Code with the LinkedIn poster prompt
        result = subprocess.run(
            [
                'ccr', 'code',
                '--allowedTools', 'Read,Glob,Grep,Skill,mcp__playwright__browser_navigate,mcp__playwright__browser_click,mcp__playwright__browser_snapshot,mcp__playwright__browser_fill_form',
                '--disallowedTools', 'Bash(rm:*,sudo:*)',
                '--no-session-persistence',
                '-p', prompt
            ],
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
            encoding='utf-8',
            errors='replace',
            shell=True
        )

        if result.returncode == 0:
            print("Successfully triggered LinkedIn post creation:")
            # Handle potential encoding issues when printing Claude's output
            try:
                print(result.stdout.encode('utf-8', errors='replace').decode('utf-8'))
            except Exception:
                print("(Output contains special characters that couldn't be displayed)")
            return True
        else:
            print(f"Failed to trigger LinkedIn post:")
            # Handle potential encoding issues when printing error output
            try:
                print(result.stderr.encode('utf-8', errors='replace').decode('utf-8'))
            except Exception:
                print("(Error output contains special characters that couldn't be displayed)")
            return False

    except subprocess.TimeoutExpired:
        print("Claude Code command timed out while posting to LinkedIn")
        return False
    except FileNotFoundError:
        print("ccr command not found, unable to trigger Claude Code for LinkedIn posting.")
        return False
    except Exception as e:
        print(f"Error triggering Claude Code for LinkedIn post: {e}")
        return False


def main():
    """
    Main function to run the LinkedIn poster script.
    """
    print("LinkedIn Poster CLI - Running Claude Code to post on LinkedIn")

    success = run_linkedin_poster()

    if success:
        print("LinkedIn post request completed successfully")
        sys.exit(0)
    else:
        print("LinkedIn post request failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
