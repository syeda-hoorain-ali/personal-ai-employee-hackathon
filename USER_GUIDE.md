# Personal AI Employee - User Guide

## Overview
The Personal AI Employee is an autonomous system that monitors your digital life and processes tasks based on predefined rules. It can watch file system changes, monitor Gmail, and take actions according to your company handbook.

## Prerequisites

### 1. Install Python
- Download and install Python 3.9 or higher from [python.org](https://www.python.org/downloads/)
- Make sure to check "Add Python to PATH" during installation
- Verify installation by opening a command prompt and typing:
  ```
  python --version
  ```

### 2. Install uv
`uv` is a fast Python package installer and resolver that we use for managing dependencies:
- Visit [https://github.com/astral-sh/uv](https://github.com/astral-sh/uv) for installation instructions
- Or install via pip: `pip install uv`
- Verify installation by opening a command prompt and typing:
  ```
  uv --version
  ```

## Setting Up Google Credentials (Optional)

If you want the AI Employee to monitor your Gmail account:

### 1. Create a Google Cloud Project
1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" at the top, then "New Project"
3. Give your project a name (e.g., "AI Employee") and click "Create"

### 2. Enable Gmail API
1. In your project dashboard, search for "Gmail API"
2. Click on "Gmail API" and then "Enable"

### 3. Configure Consent Screen
1. In the left sidebar, click "APIs & Services" > "OAuth Consent Screen"
2. Click "Configure Consent Screen"
3. If prompted with "Google Auth Platform not configured yet", click "Get Started"
4. Fill in the application information:
   - Application name: "AI Employee"
   - User support email: your email
5. Click "Next"
6. Select "External" and click "Next"
7. Fill in the application information:
   - Contact information: your email
8. Click "Next"
9. Check the "I agree" checkbox and click "Continue"
10. Click "Create"

### 4. Create OAuth 2.0 Credentials

1. From the OAuth overview page, click "Create OAuth Client"
2. If prompted with "OAuth consent screen not configured", click "Configure Consent Screen" and follow the steps in section 3 above
3. Select "Application type" as "Desktop application"
4. Give it a name (e.g., "AI Employee Desktop App")
5. Click "Create"
6. Download the credentials file and rename it to `gcp-oauth.keys.json` in the `~/.gmail-mcp/` directory

### 5. Add Your Email as a Test User
1. After creating the OAuth credentials, go back to "APIs & Services" > "OAuth consent screen" > "Audience"
2. Under the "Test users" section, click "Add users"
3. Add your email address that you'll use to authenticate
4. Click "Save" to save the changes

### 6. Place the Credentials File
- Create the `~/.gmail-mcp/` directory and copy the `gcp-oauth.keys.json` file to it

## Setting Up LinkedIn Credentials (Optional)

If you want the AI Employee to automatically post on LinkedIn:

### 1. Create the Config File
1. Navigate to the `AI_Employee_Vault` directory in your project
2. Create a file named `config.json` in this directory
3. The file structure should be: `AI_Employee_Vault/config.json`

### 2. Add Your LinkedIn Credentials
1. Open the `config.json` file in a text editor
2. Add your LinkedIn email and password in the following format:

```
{
  "linkedin": {
    "email": "YOUR_LINKEDIN_EMAIL",
    "password": "YOUR_LINKEDIN_PASSWORD"
  }
}
```

### 3. Security Note
⚠️ **Warning**: Storing credentials in plain text is a security risk. Consider the following:
- Use a strong, unique password for your LinkedIn account
- Do not commit this file to version control (it should be in your `.gitignore`)
- Consider using a dedicated LinkedIn account for automation
- Change your password regularly

### 4. Configure LinkedIn Auto-Posting
The system includes a LinkedIn poster script that can automatically post updates:
1. The script is located at `app/scripts/linkedin_poster_cli.py`
2. To schedule automatic posts, run the setup script as administrator:
   ```
   python scripts/setup.py
   ```
3. When prompted, ensure you run with administrator privileges to enable the scheduled task
4. The system will post daily at 12:00 PM if credentials are properly configured

## Running the System

### 1. Clone or Download the Project
- Get the project files to your computer

### 2. Open Command Prompt/Terminal
- Navigate to the project's root directory where `scripts` folder is located

### 3. Run the Setup and Start Script
Execute the following command:
```
python scripts/setup.py
```

This will:
- Set up the virtual environment
- Install all dependencies
- Create the vault structure with necessary directories
- Verify system components
- Automatically start the AI Employee system

### 4. System Operation
Once running, the system will:
- Monitor the `AI_Employee_Vault/Needs_Action` directory for new `.md` files
- If Gmail credentials are provided, monitor your Gmail for important emails
- Process tasks according to rules in `AI_Employee_Vault/Company_Handbook.md`
- Log activity to `AI_Employee_Vault/Dashboard.md`

### 5. How Claude Code Interacts with the System
The system is designed to work seamlessly with Claude Code:

1. **Files in Needs_Action Folder**: When the Gmail Watcher or File System Watcher detect new items, they create files in the `Needs_Action` folder.

2. **Claude Prompt Generation**: The File Processor monitor the `Needs_Action` folder and automatically run Claude Code via slash commands/skills. These prompts include:
   - The file that needs processing
   - Relevant Company Handbook rules
   - Specific instructions on how to handle the file

3. **Claude Processing**: Claude Code can monitor the `Needs_Action` folder and process each prompt according to the Company Handbook rules and it's skills.

4. **File Movement**: After Claude Code processes a file, it moves the file from `Needs_Action` to the appropriate folder (`Done`, `Pending_Approval`, etc.) based on the Company Handbook rules.

### 6. Adding Tasks
To give the AI Employee tasks:
- Create `.md` files in the `AI_Employee_Vault/Inbox` directory (preferred) or `AI_Employee_Vault/Needs_Action` directory
- The AI will process these according to the rules in your Company Handbook

### 7. Stopping the System
Press `Ctrl+C` in the terminal/command prompt to stop the system gracefully.

## Company Handbook Customization

The system uses `AI_Employee_Vault/Company_Handbook.md` to determine how to process tasks. You should customize this file with your specific rules and preferences for:
- Email response guidelines
- Financial transaction rules
- Task priority classifications
- Escalation procedures
- Approval matrix

## Troubleshooting

### Common Issues:

1. **Python not found**: Make sure Python is installed and added to your PATH
2. **uv not found**: Make sure uv is installed and accessible from command line
3. **Permission errors**: Run the command prompt as administrator (Windows) or with sudo (Linux/Mac)
4. **Import errors**: Make sure you're running from the project root directory

### Updating the System:
- To update dependencies, run: `cd app && uv sync`
- To restart the system, stop it with Ctrl+C and run `python scripts/setup.py` again

## First-Time Setup Checklist:
- [ ] Python 3.9+ installed
- [ ] uv installed
- [ ] Project files downloaded/cloned
- [ ] (Optional) Gmail credentials set up in ~/.gmail-mcp/ directory
- [ ] Run `python scripts/setup.py`
- [ ] Verify system is monitoring (check Dashboard.md for activity)
- [ ] Customize Company_Handbook.md with your preferences
- [ ] Add test tasks to Needs_Action directory to verify functionality
