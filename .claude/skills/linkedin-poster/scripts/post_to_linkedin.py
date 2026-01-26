#!/usr/bin/env python3
"""
LinkedIn Poster Script

This script automates posting to LinkedIn using Playwright.
"""

import json
import time
from pathlib import Path

def post_to_linkedin(post_content):
    """
    Automates posting to LinkedIn

    Args:
        post_content (str): The content to post on LinkedIn
    """
    try:
        # Import Playwright
        from playwright.sync_api import sync_playwright

        # Read credentials from config.json
        config_path = "C:/Users/dell/Desktop/projects/class-project/personal-ai-employee-2/AI_Employee_Vault/config.json"

        with open(config_path, 'r') as f:
            config_data = json.load(f)

        email = config_data['linkedin']['email']
        password = config_data['linkedin']['password']

        # Start Playwright
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            # Navigate to LinkedIn
            page.goto('https://www.linkedin.com')

            # Click on Login button
            page.get_by_role('link', name='Login').click()

            # Fill email and password
            page.get_by_role('textbox', name='Email or phone').fill(email)
            page.get_by_role('textbox', name='Password').fill(password)

            # Click Sign in button
            page.get_by_role('button', name='Sign in', exact=True).click()

            # Wait for login to complete
            page.wait_for_url('https://www.linkedin.com/feed/**')

            # Click on Start a post button
            page.locator('[ref="e346"]').click()  # Or use the text "Start a post"

            # Wait for post area to load
            time.sleep(2)

            # Fill the post content
            page.get_by_role('textbox', name='Text editor for creating content').fill(post_content)

            # Click Post button
            page.get_by_role('button', name='Post', exact=True).click()

            # Wait for post to be successful
            time.sleep(2)

            print("Successfully posted to LinkedIn!")

            # Close browser
            browser.close()

    except Exception as e:
        print(f"Error posting to LinkedIn: {str(e)}")
        return False

    return True

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        post_content = " ".join(sys.argv[1:])
        post_to_linkedin(post_content)
    else:
        print("Usage: python post_to_linkedin.py 'Your post content here'")