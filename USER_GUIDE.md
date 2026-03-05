# Personal AI Employee - User Guide

## Overview
The Personal AI Employee is an autonomous system that monitors your digital life and processes tasks based on predefined rules. It can watch file system changes, monitor Gmail, and take actions according to your company handbook.

## Prerequisites

### Required Prerequisites

These must be installed before running `python scripts/setup.py`:

#### 1. Install Python 3.9+
- Download and install Python 3.9 or higher from [python.org](https://www.python.org/downloads/)
- **Important**: Make sure to check "Add Python to PATH" during installation
- Verify installation by opening a command prompt and typing:
  ```
  python --version
  ```
  Should show: `Python 3.9.x` or higher

#### 2. Install uv
`uv` is a fast Python package installer and resolver that we use for managing dependencies:
- Visit [https://github.com/astral-sh/uv](https://github.com/astral-sh/uv) for installation instructions
- Or install via pip: `pip install uv`
- Verify installation by opening a command prompt and typing:
  ```
  uv --version
  ```

#### 3. Install Node.js and npm
Node.js is required for MCP servers and plugins:
- Download and install Node.js LTS from [nodejs.org](https://nodejs.org/)
- This will automatically install npm and npx
- Verify installation by opening a command prompt and typing:
  ```
  node --version
  npm --version
  npx --version
  ```

#### 4. Install Claude Code CLI
Claude Code CLI is required for MCP server registration and plugin installation:
- Install globally via npm:
  ```
  npm install -g @anthropic-ai/claude-code
  ```
- Or follow the official installation guide at [Claude Code documentation](https://docs.anthropic.com/claude/docs/claude-code)
- Verify installation by typing:
  ```
  claude --version
  ```

### Optional Prerequisites

These are optional but enable additional features:

#### Setting Up Google Credentials (Optional)

If you want the AI Employee to monitor your Gmail account:
[Gmail setup guide](/guides/gmail-setup-guide.md)

#### Setting Up LinkedIn Credentials (Optional)

If you want the AI Employee to automatically post on LinkedIn:
[Linkedin setup guide](/guides/linkedin-setup-guide.md)

#### Setting Up Odoo (Optional)

If you want the AI Employee to manage accounting, invoicing, and business operations through Odoo Community Edition:
[Odoo setup guide](/guides/ODOO_SETUP_GUIDE.md)

**Features enabled with Odoo:**
- Automated invoice creation and management
- Expense tracking and categorization
- Customer relationship management (CRM)
- Weekly CEO briefings with real-time financial data
- Payment recording and bank reconciliation
- Financial reports and business analytics

---

## Running the System

### 1. Clone or Download the Project
- Get the project files to your computer

### 2. Open Command Prompt/Terminal
- Navigate to the project's root directory where `scripts` folder is located

### 3. Configure Environment Variables
Before running the setup script, configure your environment variables:

1. Copy the example configuration file:
   ```
   cp .env.example .env
   ```
   (On Windows Command Prompt, use: `copy .env.example .env`)

2. Edit the `.env` file with your preferred text editor and fill in your values:
   - **Required for basic operation**: `VAULT_PATH`, `AGENT_NAME`
   - **Optional for other features**: See `.env.example` for all available options

3. Save the `.env` file

### 4. Run the Setup and Start Script
Execute the following command:
```
python scripts/setup.py
```

This will:
- **Sync environment variables** from your .env file to system (permanent) and session (temporary)
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

---

## Updating Environment Variables

After the initial setup, you may need to update your environment variables (e.g., adding new API keys, updating configuration).

### How to Update

1. **Edit the .env file** with your preferred text editor:
   ```
   notepad .env        # Windows
   nano .env           # Linux/Mac
   ```

2. **Run the sync script** to apply changes:
   ```
   python scripts/sync_env_vars.py
   ```

This will:
- Read all variables from your `.env` file
- Set them permanently in your system (user-level environment variables)
- Make them available in the current terminal session
- Ensure MCP servers and other components use the updated values

### Important Notes
- **Windows**: New terminals will automatically have the updated variables
- **Linux/Mac**: Run `source ~/.bashrc` or restart your terminal to load variables in existing sessions
- **MCP Servers**: Restart Claude Code or the AI Employee system for MCP servers to pick up new values
- **Security**: The sync script masks sensitive values (passwords, keys, tokens) in output for security

---

## Company Handbook Customization

The system uses `AI_Employee_Vault/Company_Handbook.md` to determine how to process tasks. You should customize this file with your specific rules and preferences for:
- Email response guidelines
- Financial transaction rules
- Task priority classifications
- Escalation procedures
- Approval matrix

## Error Recovery System

The Personal AI Employee includes a comprehensive error recovery system that automatically handles failures and maintains system reliability.

### Features

1. **Centralized Error Logging**
   - All errors are logged to daily JSON files in `AI_Employee_Vault/Logs/Errors/`
   - Error dashboard at `AI_Employee_Vault/.system/error_dashboard.json` provides real-time visibility
   - Errors are categorized by type: TRANSIENT, AUTHENTICATION, LOGIC, DATA, SYSTEM

2. **Automatic Retry with Exponential Backoff**
   - Transient errors (network timeouts, temporary service unavailability) are automatically retried
   - Uses exponential backoff: 1s, 2s, 4s delays between retries
   - Configurable retry attempts (default: 3)

3. **Circuit Breaker Pattern**
   - Prevents cascading failures by temporarily pausing failing components
   - Opens after consecutive failures (default: 3)
   - Automatically recovers after timeout period (default: 60 seconds)
   - Half-open state for gradual recovery testing

4. **Component Health Monitoring (Watchdog)**
   - Monitors critical components and automatically restarts crashed processes
   - Detects crash loops (3 crashes in 5 minutes) and pauses components
   - Exponential backoff for restart attempts
   - Configurable restart limits

5. **Operation Queuing**
   - Queues operations when external services are unavailable
   - Priority-based processing (1=highest, 3=lowest)
   - Persistent queue survives system restarts
   - Automatic processing when services recover

6. **File Quarantine**
   - Corrupted or problematic files are automatically quarantined
   - SHA-256 file hashing for integrity verification
   - Quarantined files can be restored or permanently deleted
   - Quarantine statistics tracked in dashboard

### Monitoring Error Recovery

1. **View Error Dashboard**
   ```bash
   cat AI_Employee_Vault/.system/error_dashboard.json
   ```
   Shows:
   - Error summary by component and type
   - Paused components (circuit breakers opened)
   - Quarantined files statistics

2. **View Daily Error Logs**
   ```bash
   cat AI_Employee_Vault/Logs/Errors/YYYY-MM-DD.json
   ```
   Contains detailed error entries with timestamps, context, and stack traces

3. **Check Quarantined Files**
   Quarantined files are stored in:
   ```
   AI_Employee_Vault/.system/quarantine/
   AI_Employee_Vault/.system/quarantine/metadata/
   ```

4. **View Queued Operations**
   Queued operations are stored in:
   ```
   AI_Employee_Vault/.system/queue/pending/
   AI_Employee_Vault/.system/queue/completed/
   AI_Employee_Vault/.system/queue/failed/
   ```

### Error Recovery Configuration

Error recovery components are automatically initialized with sensible defaults. Advanced users can customize:

- **Retry Configuration**: Modify `max_attempts` and `base_delay` in retry decorators
- **Circuit Breaker**: Adjust `failure_threshold` and `timeout_seconds`
- **Watchdog**: Configure `max_restart_attempts` and `crash_detection_window_minutes`
- **Queue**: Set `max_queue_size` and `max_retries` in OperationQueueConfig

### Troubleshooting Error Recovery

1. **Component Paused (Circuit Breaker Open)**
   - Check error dashboard for failure reason
   - Wait for timeout period (default: 60 seconds)
   - Circuit breaker will automatically attempt recovery

2. **Quarantined Files**
   - Review quarantine metadata to understand why file was quarantined
   - Fix file issues and restore using FileQuarantine.restore_file()
   - Or permanently delete using FileQuarantine.delete_quarantined_file()

3. **Queue Buildup**
   - Check if external services are down
   - Monitor queue size in error dashboard
   - Operations will automatically process when services recover

4. **Watchdog Restart Loops**
   - Component will be paused after 3 crashes in 5 minutes
   - Check error logs for root cause
   - Fix underlying issue before manually restarting

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

### Required Prerequisites:
- [ ] Python 3.9+ installed and added to PATH
- [ ] uv package manager installed
- [ ] Node.js and npm installed
- [ ] Claude Code CLI installed (`npm install -g @anthropic-ai/claude-code`)
- [ ] Project files downloaded/cloned

### Optional Prerequisites:
- [ ] Gmail credentials set up in ~/.gmail-mcp/ directory
- [ ] LinkedIn credentials set up in AI_Employee_Vault/config.json
- [ ] Odoo Custom Connection created and credentials added to environment

### Setup and Verification:
- [ ] Run `python scripts/setup.py` as administrator (Windows) or with sudo (Linux/Mac)
- [ ] Verify Weekly CEO Briefing scheduler created: `schtasks /query /tn WeeklyCEOBriefing` (Windows)
- [ ] Verify LinkedIn scheduler created: `schtasks /query /tn LinkedInAutoPoster` (Windows)
- [ ] Verify system is monitoring (check Dashboard.md for activity)
- [ ] Customize Company_Handbook.md with your preferences
- [ ] Update AI_Employee_Vault/Business_Goals.md with your business targets
- [ ] Add test tasks to Needs_Action directory to verify functionality
