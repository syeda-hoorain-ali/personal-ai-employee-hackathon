#!/bin/bash

# Platinum Vault Sync Setup Script
# Automates steps 1-11 from specs/006-platinum-vault-sync/quickstart.md
# Feature: 006-platinum-vault-sync
# Date: 2026-02-22

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

prompt_user() {
    echo -e "${YELLOW}?${NC} $1"
    read -p "Continue? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Setup cancelled by user"
        exit 1
    fi
}

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VAULT_PATH="$PROJECT_ROOT/AI_Employee_Vault"

echo "================================================"
echo "Platinum Vault Sync Setup"
echo "================================================"
echo ""
echo "Project Root: $PROJECT_ROOT"
echo "Vault Path: $VAULT_PATH"
echo ""

# Step 0: Check prerequisites
print_step "Step 0: Checking prerequisites..."

# Check Python
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    print_error "Python 3.12+ is required but not found"
    exit 1
fi
PYTHON_CMD=$(command -v python3 || command -v python)
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
print_success "Python $PYTHON_VERSION found"

# Check Git
if ! command -v git &> /dev/null; then
    print_error "Git is required but not found"
    exit 1
fi
GIT_VERSION=$(git --version | awk '{print $3}')
print_success "Git $GIT_VERSION found"

# Check if vault exists
if [ ! -d "$VAULT_PATH" ]; then
    print_error "Vault directory not found at: $VAULT_PATH"
    print_warning "Please create the vault directory first"
    exit 1
fi
print_success "Vault directory exists"

echo ""

# Step 1: Install dependencies
print_step "Step 1: Installing dependencies..."

cd "$PROJECT_ROOT"

# Check if uv is available
if command -v uv &> /dev/null; then
    print_success "Using uv for package installation"
    uv pip install GitPython==3.1.40 watchdog==3.0.0 pre-commit==3.5.0
else
    print_warning "uv not found, using pip"
    $PYTHON_CMD -m pip install GitPython==3.1.40 watchdog==3.0.0 pre-commit==3.5.0
fi

print_success "Dependencies installed"
echo ""

# Step 2: Create private Git repository (manual step)
print_step "Step 2: Create private Git repository"
echo ""
echo "You need to create a private Git repository for vault sync."
echo ""
echo "Option A - GitHub:"
echo "  gh repo create personal-ai-employee-vault --private --description \"AI Employee vault sync\""
echo "  OR create manually at: https://github.com/new"
echo ""
echo "Option B - GitLab:"
echo "  glab repo create personal-ai-employee-vault --private"
echo "  OR create manually at: https://gitlab.com/projects/new"
echo ""
echo "Repository settings:"
echo "  - Name: personal-ai-employee-vault (or your choice)"
echo "  - Visibility: Private"
echo "  - Do NOT initialize with README"
echo ""
prompt_user "Have you created the private repository?"

# Get repository URL
echo ""
read -p "Enter the repository URL (SSH or HTTPS): " REPO_URL
if [ -z "$REPO_URL" ]; then
    print_error "Repository URL is required"
    exit 1
fi
print_success "Repository URL: $REPO_URL"
echo ""

# Step 3: Initialize Git in vault
print_step "Step 3: Initializing Git in vault..."

cd "$VAULT_PATH"

# Check if already initialized
if [ -d ".git" ]; then
    print_warning "Git already initialized in vault"
    prompt_user "Reinitialize? This will remove existing Git history"
    rm -rf .git
fi

git init
git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL"

# Verify remote
if git remote -v | grep -q origin; then
    print_success "Git initialized and remote configured"
else
    print_error "Failed to configure Git remote"
    exit 1
fi
echo ""

# Step 4: Configure .gitignore
print_step "Step 4: Configuring .gitignore for security..."

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

print_success ".gitignore created"

# Test that .env is ignored
echo "TEST_SECRET=abc123" > .env
if git status --porcelain | grep -q ".env"; then
    print_error ".env is NOT being ignored by Git!"
    exit 1
fi
rm .env
print_success "Verified: .env files are excluded from Git"
echo ""

# Step 5: Set up pre-commit hooks
print_step "Step 5: Setting up pre-commit hooks for secret scanning..."

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
if command -v detect-secrets &> /dev/null; then
    detect-secrets scan > .secrets.baseline
    print_success "Secrets baseline created"
else
    print_warning "detect-secrets not found, skipping baseline creation"
    print_warning "Run: pip install detect-secrets && detect-secrets scan > .secrets.baseline"
fi

print_success "Pre-commit hooks configured"
echo ""

# Step 6: Create domain directory structure
print_step "Step 6: Creating domain directory structure..."

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

print_success "Domain directory structure created"
echo ""

# Step 7: Create domain configuration
print_step "Step 7: Creating domain configuration..."

mkdir -p .config

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

print_success "Domain configuration created"
echo ""

# Step 8: Initial commit and push
print_step "Step 8: Creating initial commit and pushing to remote..."

git add .

if git diff --cached --quiet; then
    print_warning "No changes to commit"
else
    git commit -m "[setup] Initialize vault sync infrastructure"
    print_success "Initial commit created"
fi

# Push to remote
echo ""
print_warning "Attempting to push to remote..."
echo "If this fails, you may need to configure SSH keys or HTTPS credentials"
echo ""

if git push -u origin main 2>&1; then
    print_success "Pushed to remote successfully"
elif git push -u origin master 2>&1; then
    print_success "Pushed to remote successfully (master branch)"
else
    print_error "Failed to push to remote"
    print_warning "You may need to configure authentication:"
    echo "  - For SSH: ssh-keygen -t ed25519 -C \"your_email@example.com\""
    echo "  - For HTTPS: git config credential.helper store"
    echo ""
    prompt_user "Continue anyway?"
fi
echo ""

# Step 9: Verify sync works
print_step "Step 9: Verifying sync works..."

# Check Git status
if [ -z "$(git status --porcelain)" ]; then
    print_success "Git status is clean"
else
    print_warning "Git status shows uncommitted changes"
fi

# Verify remote connection
if git fetch origin &> /dev/null; then
    print_success "Remote connection verified"
else
    print_warning "Could not fetch from remote"
fi

# Check that secrets are NOT in Git
if [ -z "$(git log --all --full-history --source -- .env 2>/dev/null)" ]; then
    print_success "Verified: .env is NOT in Git history"
else
    print_error ".env found in Git history!"
    exit 1
fi

if [ -z "$(git log --all --full-history --source -- credentials/ 2>/dev/null)" ]; then
    print_success "Verified: credentials/ is NOT in Git history"
else
    print_error "credentials/ found in Git history!"
    exit 1
fi
echo ""

# Step 10: Test claim protocol
print_step "Step 10: Creating test task for claim protocol..."

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

git add Needs_Action/email/test-task-001.md
git commit -m "[test] Add test task for claim protocol"

if git push 2>&1; then
    print_success "Test task created and pushed"
else
    print_warning "Test task created but not pushed (push manually later)"
fi
echo ""

# Step 11: Configure agent environment variables
print_step "Step 11: Creating .env template in project root..."

cd "$PROJECT_ROOT"

cat > .env.example << EOF
# Agent Configuration
AGENT_NAME=local-agent  # Change to "cloud-agent" on Cloud VM
VAULT_PATH=$VAULT_PATH

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

print_success ".env.example created"

# Check if .env already exists
if [ -f ".env" ]; then
    print_warning ".env already exists, not overwriting"
else
    cp .env.example .env
    print_success ".env created from template"
    print_warning "Please update VAULT_PATH and other settings in .env"
fi

# Verify .env is ignored
if git status --porcelain | grep -q "\.env$"; then
    print_error ".env is NOT being ignored by Git in project root!"
    print_warning "Add .env to project root .gitignore"
else
    print_success "Verified: .env is excluded from Git in project root"
fi
echo ""

# Final summary
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
print_success "Vault sync infrastructure is ready"
echo ""
echo "Next steps:"
echo "  1. Update .env file with your settings"
echo "  2. Test vault sync with: python test_vault_sync.py"
echo "  3. Deploy Cloud VM (Phase 1B)"
echo "  4. Review security checklist in quickstart.md"
echo ""
echo "Security checklist:"
echo "  - [ ] .env file is NOT in Git history"
echo "  - [ ] credentials/ directory is NOT in Git history"
echo "  - [ ] Pre-commit hooks are installed and working"
echo "  - [ ] Git repository is private (not public)"
echo "  - [ ] SSH keys or HTTPS credentials are secure"
echo ""
echo "For troubleshooting, see: specs/006-platinum-vault-sync/quickstart.md"
echo ""
