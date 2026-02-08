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
[Gmail setup guide](./guides/gmail-setup-guide.md)

## Setting Up LinkedIn Credentials (Optional)

If you want the AI Employee to automatically post on LinkedIn:
[Linkedin setup guide](./guides/linkedin-setup-guide.md)

## Setting Up Xero Credentials (Optional)

If you want the AI Employee to manage your accounting and financial data through Xero:
[Xero setup guide](./guides/xero-setup-guide.md)


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
- [ ] (Optional) LinkedIn credentials set up in AI_Employee_Vault/config.json
- [ ] (Optional) Xero Custom Connection created and credentials added to environment
- [ ] Run `python scripts/setup.py`
- [ ] Verify system is monitoring (check Dashboard.md for activity)
- [ ] Customize Company_Handbook.md with your preferences
- [ ] Add test tasks to Needs_Action directory to verify functionality
