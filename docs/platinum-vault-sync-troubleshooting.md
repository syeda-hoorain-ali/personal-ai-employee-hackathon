# Troubleshooting Guide: Platinum Vault Sync Infrastructure

**Feature**: 006-platinum-vault-sync
**Last Updated**: 2026-02-23
**Related Docs**: [quickstart.md](../specs/006-platinum-vault-sync/quickstart.md), [spec.md](../specs/006-platinum-vault-sync/spec.md)

## Overview

This guide helps diagnose and resolve common issues with the Platinum Tier vault synchronization infrastructure. The system uses Git-based sync between Cloud and Local agents with security boundaries, domain-based work separation, and conflict-free task claiming.

## Quick Diagnostics

Before diving into specific issues, run these quick checks:

```bash
# Check Git status
cd AI_Employee_Vault
git status

# Check remote connectivity
git fetch origin --dry-run

# Verify .gitignore is working
git check-ignore -v .env credentials/

# Check for stalled tasks
find In_Progress/ -type f -name "*.md" -mmin +30

# Review recent logs
tail -n 50 Logs/vault_sync.log
```

---

## 1. Git Sync Issues

### 1.1 Authentication Failures

**Symptoms**:
- `fatal: Authentication failed` error during push/pull
- `Permission denied (publickey)` error
- `remote: Invalid username or password` error

**Diagnosis**:
```bash
# Test SSH connection
ssh -T git@github.com

# Check Git remote URL
git remote -v

# Verify credentials
git config --list | grep credential
```

**Solutions**:

**For SSH Authentication**:
```bash
# Generate new SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add to SSH agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Copy public key and add to GitHub/GitLab
cat ~/.ssh/id_ed25519.pub

# Test connection
ssh -T git@github.com
```

**For HTTPS Authentication**:
```bash
# Configure credential helper
git config --global credential.helper store

# Or use cache (temporary)
git config --global credential.helper cache

# Update remote URL to HTTPS
git remote set-url origin https://github.com/username/repo.git

# Push (will prompt for credentials once)
git push
```

**For Personal Access Tokens (GitHub)**:
```bash
# Create token at: https://github.com/settings/tokens
# Scopes needed: repo (full control)

# Use token as password when prompted
# Username: your-github-username
# Password: ghp_xxxxxxxxxxxxxxxxxxxx
```

---

### 1.2 Network Connectivity Issues

**Symptoms**:
- `fatal: unable to access` error
- `Connection timed out` error
- Sync operations hang indefinitely
- `Could not resolve host` error

**Diagnosis**:
```bash
# Test network connectivity
ping github.com

# Test Git protocol
git ls-remote origin

# Check proxy settings
git config --get http.proxy
git config --get https.proxy

# Review network logs
tail -n 100 Logs/vault_sync.log | grep -i "network\|timeout\|connection"
```

**Solutions**:

**Temporary Network Outage**:
```bash
# The system should auto-retry with exponential backoff
# Check retry attempts in logs
grep "retry" Logs/vault_sync.log

# Manual retry after network restored
cd AI_Employee_Vault
git pull origin main
git push origin main
```

**Proxy Configuration**:
```bash
# Set proxy for Git
git config --global http.proxy http://proxy.example.com:8080
git config --global https.proxy https://proxy.example.com:8080

# Or unset if not needed
git config --global --unset http.proxy
git config --global --unset https.proxy
```

**Firewall Issues**:
```bash
# Switch from SSH to HTTPS (port 443 often allowed)
git remote set-url origin https://github.com/username/repo.git

# Or configure SSH over HTTPS
cat >> ~/.ssh/config << 'EOF'
Host github.com
    Hostname ssh.github.com
    Port 443
    User git
EOF
```

**Offline Mode**:
```bash
# Disable sync temporarily in .env
GIT_SYNC_ENABLED=false

# Agent will continue working locally
# Re-enable when network restored
GIT_SYNC_ENABLED=true
```

---

### 1.3 Git Merge Conflicts

**Symptoms**:
- `CONFLICT (content): Merge conflict in <file>` error
- Sync operations fail with unresolved conflicts
- Files contain conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)

**Diagnosis**:
```bash
# Check for conflicts
git status | grep "both modified"

# View conflicted files
git diff --name-only --diff-filter=U

# Show conflict details
git diff <conflicted-file>
```

**Solutions**:

**Dashboard.md Conflicts (Local Wins)**:
```bash
# Local agent always wins for Dashboard.md
git checkout --ours Dashboard.md
git add Dashboard.md
git commit -m "[local-agent] resolve conflict: Local wins on Dashboard.md"
git push
```

**Task File Conflicts (Manual Review)**:
```bash
# View both versions
git show :2:path/to/task.md  # Local version
git show :3:path/to/task.md  # Remote version

# Choose one version
git checkout --ours path/to/task.md   # Keep local
# OR
git checkout --theirs path/to/task.md # Keep remote

# Or manually edit to merge both
nano path/to/task.md  # Remove conflict markers

# Stage and commit
git add path/to/task.md
git commit -m "[agent-name] resolve conflict: Manual merge of task file"
git push
```

**Prevent Future Conflicts**:
```bash
# Ensure agents follow single-writer rules:
# - Local agent: writes to Dashboard.md
# - Cloud agent: writes to Updates/cloud-status-*.md
# - Both agents: claim tasks by moving (atomic operation)

# Verify domain separation
cat AI_Employee_Vault/.config/domains.yaml
```

**Abort Merge and Retry**:
```bash
# If conflicts are too complex
git merge --abort

# Pull with rebase instead
git pull --rebase origin main

# Or reset to remote state (CAUTION: loses local changes)
git fetch origin
git reset --hard origin/main
```

---

### 1.4 Large Repository Performance

**Symptoms**:
- Sync operations take >5 seconds
- `git status` is slow
- High memory usage during sync
- Clone/pull operations timeout

**Diagnosis**:
```bash
# Check repository size
du -sh AI_Employee_Vault/.git

# Count objects
git count-objects -vH

# Check for large files
git rev-list --objects --all | \
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | \
  awk '/^blob/ {print substr($0,6)}' | sort -n -k2 | tail -20

# Profile sync operation
time git pull
time git push
```

**Solutions**:

**Archive Old Tasks**:
```bash
# Move old completed tasks to separate archive repo
cd AI_Employee_Vault
mkdir -p ../vault-archive

# Move tasks older than 90 days
find Done/ -type f -name "*.md" -mtime +90 -exec mv {} ../vault-archive/ \;

# Commit cleanup
git add -A
git commit -m "[cleanup] Archive old completed tasks"
git push
```

**Enable Git Optimizations**:
```bash
# Configure Git for better performance
cd AI_Employee_Vault

# Enable file system cache
git config core.fscache true

# Enable parallel index preload
git config core.preloadindex true

# Increase pack window for better compression
git config pack.windowMemory 256m
git config pack.packSizeLimit 256m

# Run garbage collection
git gc --aggressive --prune=now
```

**Shallow Clone for Cloud Agent**:
```bash
# On Cloud VM, use shallow clone (faster initial setup)
git clone --depth 1 git@github.com:username/vault.git AI_Employee_Vault

# Fetch only recent history
git fetch --depth=100
```

**Split Large Files**:
```bash
# If logs are too large, rotate them
cd AI_Employee_Vault/Logs
gzip *.log
mv *.log.gz archive/

# Update .gitignore to exclude large logs
echo "Logs/*.log" >> .gitignore
echo "Logs/archive/" >> .gitignore
```

---

## 2. Claim Protocol Issues

### 2.1 Race Conditions (Duplicate Claims)

**Symptoms**:
- Two agents claim the same task
- Task file appears in multiple `In_Progress/` directories
- Duplicate work being performed

**Diagnosis**:
```bash
# Check for duplicate task files
cd AI_Employee_Vault
find In_Progress/ -type f -name "*.md" | sort | uniq -d

# Check Git history for simultaneous moves
git log --all --oneline --grep="claim" --since="1 hour ago"

# Review claim logs
grep "claim_task" Logs/vault_sync.log | tail -20
```

**Solutions**:

**Immediate Fix**:
```bash
# Identify which agent should keep the task
ls -la In_Progress/cloud-agent/task-001.md
ls -la In_Progress/local-agent/task-001.md

# Keep the earlier claim (check timestamps)
# Move the duplicate back to Needs_Action
mv In_Progress/local-agent/task-001.md Needs_Action/email/task-001.md

# Commit the fix
git add -A
git commit -m "[fix] Resolve duplicate claim for task-001"
git push
```

**Verify Atomic Move Implementation**:
```python
# Check that ClaimManager uses os.replace() (atomic)
# File: app/src/app/claim_protocol/claim_manager.py

# Should use:
os.replace(source_path, dest_path)  # Atomic on same filesystem

# NOT:
shutil.move(source_path, dest_path)  # Not atomic
```

**Increase Sync Frequency**:
```bash
# Reduce sync interval to catch claims faster
# In .env file:
GIT_SYNC_INTERVAL_SECONDS=60  # Sync every minute instead of 5

# Restart agents for changes to take effect
```

**Add Pre-Claim Check**:
```python
# Ensure agents pull before claiming
# In orchestrator.py, before claim_task():

git_manager.pull_changes()  # Get latest state
if not claim_validator.is_claimed(task_path):
    claim_manager.claim_task(task_path, agent_name)
```

---

### 2.2 Stalled Tasks Not Recovering

**Symptoms**:
- Tasks stuck in `In_Progress/` for hours
- Watchdog not moving stalled tasks back
- Agent crashed but task not recovered

**Diagnosis**:
```bash
# Find stalled tasks (no updates for 30+ minutes)
find AI_Employee_Vault/In_Progress/ -type f -name "*.md" -mmin +30

# Check watchdog status
grep "watchdog" Logs/vault_sync.log | tail -20

# Verify watchdog is enabled
grep "WATCHDOG_ENABLED" .env

# Check watchdog interval
grep "WATCHDOG_INTERVAL" .env
```

**Solutions**:

**Enable Watchdog**:
```bash
# In .env file
WATCHDOG_ENABLED=true
WATCHDOG_INTERVAL_SECONDS=300  # Check every 5 minutes
CLAIM_TIMEOUT_MINUTES=30

# Restart agent
```

**Manual Recovery**:
```bash
# Manually move stalled task back
cd AI_Employee_Vault

# Identify stalled task
ls -la In_Progress/cloud-agent/

# Move back to Needs_Action
mv In_Progress/cloud-agent/stalled-task.md Needs_Action/email/stalled-task.md

# Update task metadata (remove claim info)
# Edit the file to set:
# claimed_by: null
# claimed_at: null
# status: pending

# Commit recovery
git add -A
git commit -m "[watchdog] recover stalled: stalled-task"
git push
```

**Check Watchdog Logs**:
```bash
# Review watchdog activity
grep "TaskWatchdog\|RecoveryHandler" Logs/vault_sync.log

# Check for errors
grep "ERROR.*watchdog" Logs/vault_sync.log

# Verify watchdog thread is running
ps aux | grep python | grep orchestrator
```

**Adjust Timeout**:
```bash
# If tasks legitimately take longer, increase timeout
# In .env file:
CLAIM_TIMEOUT_MINUTES=60  # 1 hour instead of 30 minutes

# Restart agent
```

---

### 2.3 Task File Disappeared

**Symptoms**:
- Task file missing from `Needs_Action/`
- Agent expected to find task but it's gone
- No error in logs

**Diagnosis**:
```bash
# Check if another agent claimed it
find AI_Employee_Vault/In_Progress/ -name "missing-task.md"

# Check if it was completed
find AI_Employee_Vault/Done/ -name "missing-task*"

# Check Git history
cd AI_Employee_Vault
git log --all --full-history -- "**/missing-task.md"

# Check for accidental deletion
git log --diff-filter=D --summary | grep missing-task
```

**Solutions**:

**Task Was Claimed (Expected)**:
```bash
# This is normal behavior - another agent claimed it
# Check In_Progress directories
ls In_Progress/cloud-agent/
ls In_Progress/local-agent/

# If found, the other agent is processing it
```

**Task Was Completed**:
```bash
# Check Done directories
find Done/ -name "*missing-task*"

# View completion details
cat Done/email/missing-task-20260223.md
```

**Task Was Accidentally Deleted**:
```bash
# Restore from Git history
git log --all --full-history -- "**/missing-task.md"

# Get commit hash where it existed
git show <commit-hash>:path/to/missing-task.md > restored-task.md

# Move to appropriate location
mv restored-task.md Needs_Action/email/missing-task.md

# Commit restoration
git add Needs_Action/email/missing-task.md
git commit -m "[fix] Restore accidentally deleted task"
git push
```

---

## 3. Secret Scanning Issues

### 3.1 False Positives Blocking Commits

**Symptoms**:
- Pre-commit hook blocks legitimate files
- `detect-secrets` flags non-sensitive data
- Cannot commit valid configuration files

**Diagnosis**:
```bash
# Run detect-secrets manually
cd AI_Employee_Vault
detect-secrets scan --baseline .secrets.baseline

# Check what triggered the alert
detect-secrets audit .secrets.baseline

# View the flagged content
git diff --cached
```

**Solutions**:

**Audit and Mark as False Positive**:
```bash
# Interactive audit
detect-secrets audit .secrets.baseline

# For each finding:
# - Press 'n' if it's NOT a secret (false positive)
# - Press 'y' if it IS a secret (fix before committing)

# Save the updated baseline
git add .secrets.baseline
git commit -m "Update secrets baseline with false positives"
```

**Exclude Specific Files**:
```bash
# Update .pre-commit-config.yaml
cat >> .pre-commit-config.yaml << 'EOF'
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: |
          (?x)^(
            .*\.lock$|
            .*\.log$|
            tests/fixtures/.*|
            path/to/false-positive-file.md
          )$
EOF

# Reinstall hooks
pre-commit install
```

**Bypass for Emergency Commits** (Use Sparingly):
```bash
# Skip pre-commit hooks (CAUTION: only for emergencies)
git commit --no-verify -m "Emergency commit"

# Then immediately audit
detect-secrets scan > .secrets.baseline
detect-secrets audit .secrets.baseline
```

**Update Baseline After Fixing**:
```bash
# After removing actual secrets, regenerate baseline
detect-secrets scan > .secrets.baseline

# Commit updated baseline
git add .secrets.baseline
git commit -m "Update secrets baseline after cleanup"
```

---

### 3.2 Secrets Found in Git History

**Symptoms**:
- Audit script reports secrets in history
- `truffleHog` finds exposed credentials
- `.env` file or credentials committed in past

**Diagnosis**:
```bash
# Run comprehensive audit
bash scripts/audit_git_secrets.sh

# Check specific file in history
git log --all --full-history -- .env

# Search for API keys in diffs
git log -p | grep -i "api_key\|secret\|password"
```

**Solutions**:

**Immediate Actions (CRITICAL)**:
```bash
# 1. ROTATE/INVALIDATE exposed credentials immediately
# - Change passwords
# - Regenerate API keys
# - Revoke tokens
# - Update all systems using those credentials

# 2. Verify current state is clean
git status
git check-ignore -v .env credentials/
```

**Remove Secrets from History**:
```bash
# Install git-filter-repo
pip install git-filter-repo

# Backup repository first
cd ..
cp -r AI_Employee_Vault AI_Employee_Vault.backup

# Remove specific file from all history
cd AI_Employee_Vault
git filter-repo --path .env --invert-paths

# Or remove specific directory
git filter-repo --path credentials/ --invert-paths

# Force push to remote (coordinate with team first!)
git push origin --force --all
git push origin --force --tags
```

**Alternative: BFG Repo-Cleaner**:
```bash
# Install BFG
# Download from: https://rtyley.github.io/bfg-repo-cleaner/

# Remove files by name
java -jar bfg.jar --delete-files .env AI_Employee_Vault.git

# Remove files by pattern
java -jar bfg.jar --delete-files '*.key' AI_Employee_Vault.git

# Clean up
cd AI_Employee_Vault
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push origin --force --all
```

**Prevent Future Leaks**:
```bash
# Verify .gitignore is comprehensive
cat AI_Employee_Vault/.gitignore

# Ensure pre-commit hooks are installed
cd AI_Employee_Vault
pre-commit install

# Test hooks work
echo "API_KEY=secret123" > test.env
git add test.env
git commit -m "test"  # Should be blocked
rm test.env
```

**Run Regular Audits**:
```bash
# Schedule weekly audits (cron job)
crontab -e

# Add line:
0 2 * * 0 /path/to/scripts/audit_git_secrets.sh

# Or run manually weekly
bash scripts/audit_git_secrets.sh
```

---

## 4. Domain Access Errors

### 4.1 Agent Cannot Access Domain

**Symptoms**:
- `DomainAccessError: Agent not authorized for domain`
- Cloud agent trying to access `local-only/` tasks
- Tasks being skipped unexpectedly

**Diagnosis**:
```bash
# Check domain configuration
cat AI_Employee_Vault/.config/domains.yaml

# Check agent configuration
grep "ALLOWED_DOMAINS" .env
grep "AGENT_NAME" .env

# Review access logs
grep "DomainAccessError\|domain.*denied" Logs/vault_sync.log
```

**Solutions**:

**Verify Agent Configuration**:
```bash
# In .env file for LOCAL agent:
AGENT_NAME=local-agent
ALLOWED_DOMAINS=email,social,local-only

# In .env file for CLOUD agent:
AGENT_NAME=cloud-agent
ALLOWED_DOMAINS=email,social  # NO local-only access

# Restart agent after changes
```

**Update Domain Configuration**:
```bash
# Edit domains.yaml
nano AI_Employee_Vault/.config/domains.yaml

# Ensure cloud_access is set correctly:
domains:
  email:
    cloud_access: true    # Cloud can access
  social:
    cloud_access: true    # Cloud can access
  local-only:
    cloud_access: false   # Cloud CANNOT access

# Commit changes
git add .config/domains.yaml
git commit -m "[config] Update domain access rules"
git push
```

**Move Misplaced Tasks**:
```bash
# If task is in wrong domain directory
mv Needs_Action/local-only/email-task.md Needs_Action/email/email-task.md

# Update task metadata
# Edit file to set: domain: email

# Commit fix
git add -A
git commit -m "[fix] Move task to correct domain"
git push
```

---

### 4.2 Invalid Domain in Task File

**Symptoms**:
- Task file has invalid domain in YAML frontmatter
- Agent skips task with warning
- Domain validation errors in logs

**Diagnosis**:
```bash
# Check task file metadata
head -20 Needs_Action/email/problematic-task.md

# Validate against domains.yaml
cat AI_Employee_Vault/.config/domains.yaml | grep -A 5 "domains:"

# Check validation logs
grep "invalid.*domain\|domain.*validation" Logs/vault_sync.log
```

**Solutions**:

**Fix Task Metadata**:
```bash
# Edit task file
nano Needs_Action/email/problematic-task.md

# Ensure YAML frontmatter has valid domain:
---
id: task-001
domain: email  # Must be: email, social, or local-only
priority: medium
created: 2026-02-23T10:00:00Z
claimed_by: null
claimed_at: null
status: pending
---

# Commit fix
git add Needs_Action/email/problematic-task.md
git commit -m "[fix] Correct domain metadata in task file"
git push
```

**Validate All Tasks**:
```bash
# Script to check all task files
cd AI_Employee_Vault

for file in $(find Needs_Action Pending_Approval In_Progress -name "*.md"); do
    domain=$(grep "^domain:" "$file" | awk '{print $2}')
    if [[ ! "$domain" =~ ^(email|social|local-only)$ ]]; then
        echo "Invalid domain in: $file (domain: $domain)"
    fi
done
```

---

## 5. Dashboard Merge Conflicts

### 5.1 Concurrent Dashboard Updates

**Symptoms**:
- Merge conflict on `Dashboard.md`
- Both agents trying to write to Dashboard
- Sync fails with conflict error

**Diagnosis**:
```bash
# Check for Dashboard conflicts
cd AI_Employee_Vault
git status | grep Dashboard.md

# View conflict
git diff Dashboard.md

# Check who last modified
git log -1 --pretty=format:"%an %ai" Dashboard.md
```

**Solutions**:

**Resolve with Local Wins**:
```bash
# Local agent always wins for Dashboard.md
git checkout --ours Dashboard.md
git add Dashboard.md
git commit -m "[local-agent] resolve conflict: Local wins on Dashboard.md"
git push
```

**Verify Single-Writer Rule**:
```bash
# Check that Cloud agent uses Updates/ directory
grep "CloudUpdateWriter" app/src/app/dashboard_manager/cloud_update_writer.py

# Verify Local agent merges updates
grep "UpdateMerger" app/src/app/dashboard_manager/update_merger.py

# Check agent configuration
grep "AGENT_NAME" .env
```

**Fix Cloud Agent Configuration**:
```python
# In orchestrator.py for Cloud agent:
if agent_name == "cloud-agent":
    # Cloud writes to Updates/, NOT Dashboard.md
    cloud_writer.write_status_update(status_data)
else:
    # Local writes directly to Dashboard.md
    dashboard_manager.update_dashboard(status_data)
```

---

### 5.2 Updates Not Being Merged

**Symptoms**:
- Cloud status updates accumulate in `Updates/`
- Dashboard.md not reflecting Cloud agent activity
- Updates directory growing large

**Diagnosis**:
```bash
# Check for unmerged updates
ls -la AI_Employee_Vault/Updates/*.md | wc -l

# Check merge frequency
grep "DASHBOARD_MERGE_INTERVAL" .env

# Review merge logs
grep "UpdateMerger\|merge_updates" Logs/vault_sync.log
```

**Solutions**:

**Manual Merge**:
```bash
# Run merge manually
cd AI_Employee_Vault

# Read all updates
for update in Updates/cloud-status-*.md; do
    echo "Processing: $update"
    cat "$update"
    echo "---"
done

# Append to Dashboard.md
cat Updates/cloud-status-*.md >> Dashboard.md

# Archive processed updates
mv Updates/cloud-status-*.md Updates/archive/

# Commit merge
git add -A
git commit -m "[local-agent] merge: Cloud status updates to Dashboard"
git push
```

**Increase Merge Frequency**:
```bash
# In .env file for Local agent:
DASHBOARD_MERGE_INTERVAL_SECONDS=60  # Merge every minute

# Restart Local agent
```

**Verify Merger is Running**:
```python
# Check orchestrator.py has merge loop
# Should have periodic call to:
update_merger.merge_updates_to_dashboard()
```

---

## 6. General Debugging

### 6.1 Enable Verbose Logging

```bash
# In .env file:
LOG_LEVEL=DEBUG

# Or set for specific modules:
VAULT_SYNC_LOG_LEVEL=DEBUG
CLAIM_PROTOCOL_LOG_LEVEL=DEBUG

# Restart agent
```

### 6.2 Check System Health

```bash
# Run health check script
cd AI_Employee_Vault

# Check Git status
git status

# Check remote sync
git fetch origin --dry-run

# Check for stalled tasks
find In_Progress/ -type f -mmin +30

# Check disk space
df -h .

# Check for large files
du -sh * | sort -h | tail -10
```

### 6.3 Reset to Clean State

```bash
# CAUTION: This will lose uncommitted changes

# Backup first
cd ..
cp -r AI_Employee_Vault AI_Employee_Vault.backup

# Reset to remote state
cd AI_Employee_Vault
git fetch origin
git reset --hard origin/main
git clean -fd

# Verify clean state
git status
```

---

## Support Resources

- **Quickstart Guide**: `specs/006-platinum-vault-sync/quickstart.md`
- **Architecture Plan**: `specs/006-platinum-vault-sync/plan.md`
- **Feature Spec**: `specs/006-platinum-vault-sync/spec.md`
- **Audit Script**: `scripts/audit_git_secrets.sh`
- **Logs Directory**: `Logs/vault_sync.log`

## Emergency Contacts

If you encounter critical issues:

1. Check error recovery logs: `Logs/Errors/`
2. Review Git history: `git log --oneline -20`
3. Run security audit: `bash scripts/audit_git_secrets.sh`
4. Consult spec edge cases: `specs/006-platinum-vault-sync/spec.md` (Edge Cases section)

---

**Last Updated**: 2026-02-23
**Version**: 1.0
**Maintainer**: AI Employee Development Team
