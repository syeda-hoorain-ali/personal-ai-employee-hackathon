# Quickstart Guide: Bronze Tier - Personal AI Employee Foundation

## Prerequisites
- Claude Code (Pro subscription or free via Claude Code Router)
- Obsidian v1.10.6+ (free)
- Python 3.13 or higher
- Node.js v24+ LTS
- Github Desktop (latest stable)

## Setup Instructions

### 1. Initialize the Obsidian Vault
1. Create a new Obsidian vault named "AI_Employee_Vault"
2. Create the following files and folders:
   - `Dashboard.md` - Main dashboard file
   - `Company-Handbook.md` - Operational guidelines
   - `/Inbox` - Incoming items folder
   - `/Needs-Action` - Items requiring processing
   - `/Done` - Completed items folder
   - `/Plans` - Planning documents
   - `/Pending-Approval` - Items awaiting approval
   - `/Approved` - Approved items
   - `/Rejected` - Rejected items
   - `/Logs` - Log files
   - `/Accounting` - Financial records

### 2. Configure Claude Code
1. Point Claude Code to the AI_Employee_Vault directory
2. Ensure Claude Code has file system access permissions
3. Test Claude Code's ability to read and write to the vault

### 3. Set up the File System Watcher
1. Install the Python watchdog library: `pip install watchdog`
2. Create the file system watcher script to monitor `/Needs-Action` directory
3. Configure the watcher to trigger Claude Code processing when new files appear

### 4. Test the System
1. Place a test file in `/Needs-Action` directory
2. Verify the file system watcher detects the change
3. Confirm Claude Code processes the file appropriately
4. Check that processed files move to the `/Done` directory

## Basic Usage
- Add new tasks to the `/Needs-Action` directory
- Review and approve items in `/Pending-Approval` as needed
- Monitor activity through the `Dashboard.md` file
- Adjust operational rules in `Company-Handbook.md`