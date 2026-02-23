# Quickstart Guide: Platinum Tier Phase 1A - Vault Sync Infrastructure

**Feature**: 006-platinum-vault-sync
**Date**: 2026-02-22
**Audience**: Developers setting up Cloud-Local vault synchronization

## Prerequisites

Before starting, ensure you have:

- ✅ Python 3.12+ installed
- ✅ Git 2.x+ installed and configured
- ✅ GitHub/GitLab account with private repository access
- ✅ SSH keys or HTTPS credentials configured for Git
- ✅ Bronze, Silver, and Gold tier features implemented
- ✅ Existing vault at `AI_Employee_Vault/`

## Step 1: Install Dependencies

```bash
# Navigate to project root
cd personal-ai-employee

# Install new dependencies
pip install GitPython==3.1.40
pip install watchdog==3.0.0
pip install pre-commit==3.5.0

# Or using uv (recommended)
uv pip install GitPython==3.1.40 watchdog==3.0.0 pre-commit==3.5.0
```

## Step 2: Create Private Git Repository

### Option A: GitHub

```bash
# Create private repository via GitHub CLI
gh repo create personal-ai-employee-vault --private --description "AI Employee vault sync"

# Or create manually at https://github.com/new
# - Name: personal-ai-employee-vault
# - Visibility: Private
# - Do NOT initialize with README
```

### Option B: GitLab

```bash
# Create private repository via GitLab CLI
glab repo create personal-ai-employee-vault --private

# Or create manually at https://gitlab.com/projects/new
# - Name: personal-ai-employee-vault
# - Visibility: Private
```

## Step 3: Initialize Git in Vault

```bash
# Navigate to vault directory
cd AI_Employee_Vault

# Initialize Git repository
git init

# Add remote (replace with your repository URL)
git remote add origin git@github.com:yourusername/personal-ai-employee-vault.git

# Verify remote
git remote -v
```

## Step 4: Configure .gitignore for Security

Create or update `.gitignore` in vault root:

```bash
# Navigate to vault root
cd AI_Employee_Vault

# Create .gitignore
cat > .gitignore << 'EOF'
# Secrets and credentials (NEVER commit these)
.env
.env.*
!.env.example
credentials/
sessions/
*.token
*.key
*.pem
gmail_credentials.json
token.pickle

# System files
.DS_Store
Thumbs.db
*.swp
*.swo
*~

# Logs (optional - include if you want to sync logs)
# *.log
# Logs/

# Temporary files
tmp/
temp/
*.tmp
EOF
```

**Critical**: Verify secrets are excluded:

```bash
# Test that .env is ignored
echo "TEST_SECRET=abc123" > .env
git status  # Should NOT show .env

# Clean up test
rm .env
```

## Step 5: Set Up Pre-Commit Hooks for Secret Scanning

```bash
# Navigate to vault root
cd AI_Employee_Vault

# Create pre-commit configuration
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: |
          (?x)^(
            .*\.lock$|
            .*\.log$|
            tests/fixtures/.*
          )$
EOF

# Install pre-commit hooks
pre-commit install

# Create initial secrets baseline
detect-secrets scan > .secrets.baseline

# Test pre-commit hook
git add .pre-commit-config.yaml .secrets.baseline
git commit -m "Add secret scanning pre-commit hook"
```

## Step 6: Create Domain Directory Structure

```bash
# Navigate to vault root
cd AI_Employee_Vault

# Create domain subdirectories
mkdir -p Needs_Action/email
mkdir -p Needs_Action/social
mkdir -p Needs_Action/local-only

mkdir -p Pending_Approval/email
mkdir -p Pending_Approval/social

mkdir -p In_Progress/cloud-agent
mkdir -p In_Progress/local-agent

mkdir -p Updates
mkdir -p Updates/archive

mkdir -p Done/email
mkdir -p Done/social
mkdir -p Done/local-only

# Create .gitkeep files to track empty directories
find Needs_Action Pending_Approval In_Progress Updates Done -type d -exec touch {}/.gitkeep \;

# Verify structure
tree -L 2 .
```

## Step 7: Create Domain Configuration

```bash
# Create config directory
mkdir -p .config

# Create domain configuration
cat > .config/domains.yaml << 'EOF'
domains:
  email:
    description: "Email triage, drafting, and sending"
    cloud_access: true
    local_access: true
    requires_approval: true
    approval_threshold: all

  social:
    description: "Social media post drafting and scheduling"
    cloud_access: true
    local_access: true
    requires_approval: true
    approval_threshold: all

  local-only:
    description: "Sensitive operations (payments, WhatsApp, banking)"
    cloud_access: false
    local_access: true
    requires_approval: false
    approval_threshold: none

agent_config:
  cloud-agent:
    allowed_domains:
      - email
      - social
    can_draft: true
    can_send: false

  local-agent:
    allowed_domains:
      - email
      - social
      - local-only
    can_draft: true
    can_send: true
EOF
```

## Step 8: Initial Commit and Push

```bash
# Stage all files
git add .

# Create initial commit
git commit -m "[setup] Initialize vault sync infrastructure"

# Push to remote
git push -u origin main
```

## Step 9: Verify Sync Works

```bash
# Check Git status
git status  # Should be clean

# Verify remote connection
git fetch origin

# Check that secrets are NOT in Git
git log --all --full-history --source -- .env  # Should be empty
git log --all --full-history --source -- credentials/  # Should be empty
```

## Step 10: Test Claim Protocol (Local Only)

Create a test task to verify the claim protocol works:

```bash
# Create test task
cat > Needs_Action/email/test-task-001.md << 'EOF'
---
id: test-task-001
domain: email
priority: medium
created: 2026-02-22T10:00:00Z
claimed_by: null
claimed_at: null
status: pending
source: manual
---

# Test Task: Verify Claim Protocol

This is a test task to verify the claim-by-move protocol works correctly.

## Action Required
- Agent should claim this task by moving to In_Progress/
- Verify only one agent can claim
- Complete by moving to Done/
EOF

# Commit test task
git add Needs_Action/email/test-task-001.md
git commit -m "[test] Add test task for claim protocol"
git push

# Manually test claim (simulate agent)
mv Needs_Action/email/test-task-001.md In_Progress/local-agent/test-task-001.md

# Verify claim
ls In_Progress/local-agent/  # Should show test-task-001.md
ls Needs_Action/email/  # Should NOT show test-task-001.md

# Complete task
mv In_Progress/local-agent/test-task-001.md Done/email/test-task-001-$(date +%Y%m%d).md

# Commit completion
git add -A
git commit -m "[local-agent] complete email: Test claim protocol"
git push
```

## Step 11: Configure Agent Environment Variables

Create `.env` file in project root (NOT in vault):

```bash
# Navigate to project root
cd personal-ai-employee

# Create .env file
cat > .env << 'EOF'
# Agent Configuration
AGENT_NAME=local-agent  # Change to "cloud-agent" on Cloud VM
VAULT_PATH=/absolute/path/to/AI_Employee_Vault

# Git Sync Configuration
GIT_SYNC_ENABLED=true
GIT_SYNC_INTERVAL_SECONDS=300  # 5 minutes
GIT_COMMIT_MESSAGE_PREFIX=[local-agent]  # Change to [cloud-agent] on Cloud

# Claim Protocol Configuration
CLAIM_TIMEOUT_MINUTES=30
WATCHDOG_ENABLED=true
WATCHDOG_INTERVAL_SECONDS=300  # 5 minutes

# Domain Access (comma-separated)
ALLOWED_DOMAINS=email,social,local-only  # Change to "email,social" on Cloud
EOF

# Verify .env is ignored by Git
git status  # Should NOT show .env
```

## Step 12: Run Vault Sync Test

Test the sync infrastructure with Python:

```python
# Create test script: test_vault_sync.py
from pathlib import Path
from app.src.app.vault_sync.git_manager import GitManager

# Initialize Git manager
vault_path = Path("/absolute/path/to/AI_Employee_Vault")
git_manager = GitManager(vault_path)

# Test sync
result = git_manager.sync_vault(
    commit_message="[local-agent] test sync: Verify sync infrastructure"
)

print(f"Sync successful: {result['success']}")
print(f"Files changed: {result['files_changed']}")
print(f"Duration: {result['sync_duration_ms']}ms")
```

Run the test:

```bash
python test_vault_sync.py
```

## Troubleshooting

### Issue: Git push fails with authentication error

**Solution**: Configure SSH keys or HTTPS credentials

```bash
# For SSH (recommended)
ssh-keygen -t ed25519 -C "your_email@example.com"
cat ~/.ssh/id_ed25519.pub  # Add to GitHub/GitLab

# For HTTPS
git config credential.helper store
git push  # Enter credentials once, then cached
```

### Issue: Pre-commit hook blocks legitimate file

**Solution**: Update secrets baseline

```bash
# Audit the file
detect-secrets audit .secrets.baseline

# Mark as false positive in baseline
# Then commit again
```

### Issue: Merge conflict on Dashboard.md

**Solution**: Local agent wins (by design)

```bash
# Resolve conflict with local version
git checkout --ours Dashboard.md
git add Dashboard.md
git commit -m "[local-agent] resolve conflict: Local wins on Dashboard.md"
git push
```

### Issue: Task file disappeared during claim

**Solution**: Another agent claimed it (expected behavior)

```bash
# Check In_Progress directories
ls In_Progress/cloud-agent/
ls In_Progress/local-agent/

# Task should be in one of these directories
```

## Next Steps

1. ✅ Vault sync infrastructure is ready
2. ⏭️ Deploy Cloud VM (Phase 1B)
3. ⏭️ Implement work-zone specialization in agents (Phase 1C)
4. ⏭️ Test Platinum demo: offline email handling (Phase 1D)

## Security Checklist

Before deploying to Cloud, verify:

- [ ] `.env` file is NOT in Git history
- [ ] `credentials/` directory is NOT in Git history
- [ ] `sessions/` directory is NOT in Git history
- [ ] Pre-commit hooks are installed and working
- [ ] Git repository is private (not public)
- [ ] SSH keys or HTTPS credentials are secure
- [ ] Domain configuration restricts Cloud access to email/social only

## Performance Benchmarks

Expected performance for Phase 1A:

- Git sync: <5 seconds for 1,000 files ✅
- Claim operation: <100ms ✅
- Watchdog scan: <1 second for 100 tasks ✅
- Secret scan: <2 seconds per commit ✅

## Support

If you encounter issues:

1. Check logs in `Logs/` directory
2. Verify Git status: `git status`
3. Check remote connection: `git fetch origin`
4. Review error recovery logs: `Logs/Errors/`
5. Consult `specs/006-platinum-vault-sync/plan.md` for architecture details

---

**Congratulations!** Your vault sync infrastructure is ready for Cloud-Local coordination.
