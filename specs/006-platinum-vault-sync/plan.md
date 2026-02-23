# Implementation Plan: Platinum Tier Phase 1A - Vault Sync Infrastructure

**Branch**: `006-platinum-vault-sync` | **Date**: 2026-02-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-platinum-vault-sync/spec.md`

## Summary

Implement foundational infrastructure for Cloud-Local agent coordination through Git-based vault synchronization. This phase establishes security boundaries (secrets never sync), domain-based directory structure (email/social/local-only), claim-by-move protocol (prevent duplicate work), and single-writer rules (prevent merge conflicts). Enables future Cloud deployment while maintaining Local-exclusive access to sensitive operations.

**Technical Approach**: Extend existing Python vault infrastructure with GitPython for sync operations, file-based claim protocol using atomic moves, watchdog for crash recovery, and pre-commit hooks for secret scanning.

## Technical Context

**Language/Version**: Python 3.12 (existing project standard)
**Primary Dependencies**:
- GitPython 3.1+ (Git operations)
- pathlib (file operations)
- watchdog 3.0+ (file system monitoring for stalled tasks)
- pre-commit 3.5+ (secret scanning hooks)
- Existing: vault_reader, vault_writer, error_recovery modules

**Storage**: File-based vault directory structure (existing AI_Employee_Vault/)
**Testing**: pytest (existing test infrastructure)
**Target Platform**: Cross-platform (Windows/Linux) - must work on Local machine and Cloud VM
**Project Type**: Single project (extending existing app/ structure)

**Performance Goals**:
- Git sync operations complete in <5 seconds for vaults with up to 1,000 files
- Claim operations atomic (no race conditions)
- Watchdog detects stalled tasks within 30 minutes

**Constraints**:
- Zero secrets in Git history (security requirement)
- Zero task duplication with concurrent agents (correctness requirement)
- Zero merge conflicts on Dashboard.md (reliability requirement)
- Must work with intermittent network connectivity

**Scale/Scope**:
- Support up to 10,000 files in vault
- Handle 2 concurrent agents (Cloud + Local)
- Process 100+ tasks per day without conflicts

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: Constitution file is currently a template. Applying general software engineering principles:

### Principles Applied

✅ **Simplicity**: File-based claim protocol (no database), Git for sync (standard tool)
✅ **Testability**: Each component independently testable (sync, claim, watchdog)
✅ **Security-First**: Secrets excluded via .gitignore, pre-commit hooks prevent leakage
✅ **Error Recovery**: Watchdog recovers from crashes, retry logic for network failures
✅ **Observability**: Structured logging for all sync operations, audit trail in Git history

### Gates

- **No unnecessary abstractions**: Using GitPython directly, no custom VCS abstraction
- **No premature optimization**: Simple file moves for claims, optimize only if performance issues arise
- **Test coverage required**: Unit tests for sync logic, integration tests for concurrent agents
- **Documentation required**: Quickstart guide, protocol documentation, troubleshooting guide

**Status**: ✅ PASSED - No violations, approach aligns with simplicity and testability principles

## Project Structure

### Documentation (this feature)

```text
specs/006-platinum-vault-sync/
├── plan.md              # This file
├── research.md          # Phase 0: GitPython patterns, conflict resolution, secret scanning
├── data-model.md        # Phase 1: Task file format, domain config, claim state
├── quickstart.md        # Phase 1: Setup guide for Git sync
├── contracts/           # Phase 1: Sync operation contracts
│   ├── vault-sync.yaml      # Git sync operations
│   ├── claim-protocol.yaml  # Task claiming operations
│   └── watchdog.yaml        # Stalled task recovery
└── tasks.md             # Phase 2: Implementation tasks (created by /sp.tasks)
```

### Source Code (repository root)

```text
app/src/app/
├── vault_sync/                    # NEW: Git synchronization module
│   ├── __init__.py
│   ├── git_manager.py            # GitPython wrapper for sync operations
│   ├── conflict_resolver.py      # Merge conflict resolution strategies
│   └── secret_scanner.py         # Pre-commit hook for secret detection
│
├── domain_manager/                # NEW: Domain-based routing
│   ├── __init__.py
│   ├── domain_config.py          # Domain definitions (email/social/local-only)
│   └── domain_router.py          # Route tasks to authorized agents
│
├── claim_protocol/                # NEW: Task claiming logic
│   ├── __init__.py
│   ├── claim_manager.py          # Atomic file moves for claiming
│   └── claim_validator.py        # Verify claim ownership
│
├── watchdog/                      # NEW: Stalled task recovery
│   ├── __init__.py
│   ├── task_watchdog.py          # Monitor In_Progress/ for stalled tasks
│   └── recovery_handler.py       # Move stalled tasks back to Needs_Action/
│
├── dashboard_manager/             # NEW: Dashboard single-writer logic
│   ├── __init__.py
│   ├── update_merger.py          # Merge Updates/ into Dashboard.md
│   └── cloud_update_writer.py    # Cloud agent writes to Updates/
│
└── orchestrator.py                # MODIFIED: Add sync cycle hooks

AI_Employee_Vault/                 # MODIFIED: Add domain subdirectories
├── Needs_Action/
│   ├── email/                    # NEW: Email triage tasks
│   ├── social/                   # NEW: Social media tasks
│   └── local-only/               # NEW: Local-exclusive tasks
├── Pending_Approval/
│   ├── email/                    # NEW: Email draft approvals
│   └── social/                   # NEW: Social post approvals
├── In_Progress/
│   ├── cloud-agent/              # NEW: Cloud-claimed tasks
│   └── local-agent/              # NEW: Local-claimed tasks
├── Updates/                       # NEW: Cloud status updates
│   └── archive/                  # NEW: Processed updates
├── Done/
│   ├── email/                    # NEW: Completed email tasks
│   ├── social/                   # NEW: Completed social tasks
│   └── local-only/               # NEW: Completed local tasks
└── .git/                         # NEW: Git repository

.gitignore                         # MODIFIED: Add secret exclusions
.pre-commit-config.yaml           # NEW: Secret scanning hooks

tests/
├── vault_sync/                   # NEW: Sync operation tests
│   ├── test_git_manager.py
│   ├── test_conflict_resolver.py
│   └── test_secret_scanner.py
├── claim_protocol/               # NEW: Claim protocol tests
│   ├── test_claim_manager.py
│   └── test_concurrent_claims.py
└── integration/                  # NEW: End-to-end tests
    ├── test_cloud_local_sync.py
    └── test_crash_recovery.py
```

**Structure Decision**: Extending existing single-project structure with new modules for vault sync capabilities. Keeping all Python code under `app/src/app/` maintains consistency with existing architecture. Domain subdirectories added to vault for work-zone specialization.

## Complexity Tracking

> **No violations - this section intentionally left empty**

All design decisions align with simplicity principles:
- File-based claim protocol (no database)
- Standard Git for sync (no custom VCS)
- Atomic file moves (no distributed locking)
- Single-writer rule (no conflict resolution complexity)

## Phase 0: Research & Decisions

### Research Tasks

1. **GitPython Atomic Operations**
   - Research: Best practices for atomic commit/push/pull cycles
   - Research: Handling network failures and retry strategies
   - Research: Performance optimization for large repos (1,000+ files)
   - Decision needed: Sync frequency (after each operation vs. periodic batching)

2. **File-Based Claim Protocol**
   - Research: Atomic file move operations in Python (os.rename vs. shutil.move)
   - Research: Race condition prevention with concurrent file operations
   - Research: Cross-platform compatibility (Windows vs. Linux file locking)
   - Decision needed: Claim timeout duration (30 minutes vs. configurable)

3. **Git Conflict Resolution**
   - Research: Merge strategies for concurrent file modifications
   - Research: Conflict detection and resolution automation
   - Research: Local-wins strategy implementation for Dashboard.md
   - Decision needed: Manual review process for non-Dashboard conflicts

4. **Secret Scanning**
   - Research: Pre-commit hook frameworks (pre-commit, husky alternatives)
   - Research: Secret detection patterns (regex, entropy-based, tool comparison)
   - Research: Git history scanning tools (git-secrets, truffleHog, gitleaks)
   - Decision needed: Block commits vs. warn-only mode

5. **Watchdog Implementation**
   - Research: File system monitoring libraries (watchdog vs. polling)
   - Research: Stalled task detection heuristics (last modified time, metadata)
   - Research: Recovery strategies (retry vs. quarantine)
   - Decision needed: Watchdog check interval (5 minutes vs. 15 minutes)

### Expected Outputs

- `research.md` with decisions for all 5 research areas
- Rationale for chosen approaches
- Alternatives considered and rejected
- Performance implications documented

## Phase 1: Design & Contracts

### Data Models

**File**: `data-model.md`

1. **Task File Format**
   ```yaml
   ---
   id: task-001
   domain: email | social | local-only
   priority: high | medium | low
   created: 2026-02-22T10:30:00Z
   claimed_by: cloud-agent | local-agent | null
   claimed_at: 2026-02-22T10:35:00Z | null
   status: pending | in_progress | completed
   ---

   # Task Description
   [Markdown content]
   ```

2. **Domain Configuration**
   ```yaml
   domains:
     email:
       cloud_access: true
       local_access: true
       requires_approval: true
     social:
       cloud_access: true
       local_access: true
       requires_approval: true
     local-only:
       cloud_access: false
       local_access: true
       requires_approval: false
   ```

3. **Agent Claim State**
   - Represented by file location: `In_Progress/<agent>/task-001.md`
   - No separate state file needed (filesystem is source of truth)

4. **Cloud Status Update Format**
   ```yaml
   ---
   timestamp: 2026-02-22T10:40:00Z
   agent: cloud-agent
   type: status | approval_request | notification
   ---

   # Update Content
   [Markdown content]
   ```

### API Contracts

**Directory**: `contracts/`

1. **vault-sync.yaml** - Git synchronization operations
   ```yaml
   operations:
     - name: sync_vault
       description: Pull latest changes, commit local changes, push to remote
       inputs:
         - vault_path: string
         - commit_message: string
       outputs:
         - success: boolean
         - conflicts: list[string]
       errors:
         - NetworkError: Network connectivity issues
         - ConflictError: Merge conflicts detected
   ```

2. **claim-protocol.yaml** - Task claiming operations
   ```yaml
   operations:
     - name: claim_task
       description: Atomically move task from Needs_Action to In_Progress
       inputs:
         - task_path: string
         - agent_name: string
       outputs:
         - success: boolean
         - claim_path: string
       errors:
         - AlreadyClaimedError: Task already in In_Progress
         - DomainAccessError: Agent not authorized for domain
   ```

3. **watchdog.yaml** - Stalled task recovery
   ```yaml
   operations:
     - name: check_stalled_tasks
       description: Scan In_Progress for tasks with no updates for 30+ minutes
       inputs:
         - vault_path: string
         - timeout_minutes: integer
       outputs:
         - stalled_tasks: list[string]
       actions:
         - Move stalled tasks back to Needs_Action/<domain>/
   ```

### Quickstart Guide

**File**: `quickstart.md`

1. **Setup Git Sync**
   - Initialize Git repo in vault
   - Configure remote repository
   - Set up SSH keys or HTTPS credentials
   - Verify .gitignore excludes secrets

2. **Create Domain Directories**
   - Run setup script to create subdirectories
   - Verify directory structure

3. **Configure Agents**
   - Set agent name (cloud-agent vs. local-agent)
   - Configure domain access permissions
   - Set sync frequency

4. **Test Sync**
   - Create test task file
   - Verify sync to remote
   - Test claim protocol with two agents

### Agent Context Update

Run: `.specify/scripts/bash/update-agent-context.sh claude`

**Technologies to add**:
- GitPython 3.1+ (Git operations)
- watchdog 3.0+ (file system monitoring)
- pre-commit 3.5+ (secret scanning)

## Phase 2: Task Breakdown

**Note**: Task breakdown is created by `/sp.tasks` command (not part of `/sp.plan`).

Expected task categories:
1. Security & .gitignore setup
2. Directory structure creation
3. Git sync module implementation
4. Claim protocol implementation
5. Watchdog implementation
6. Dashboard manager implementation
7. Integration testing
8. Documentation

## Implementation Notes

### Critical Path

1. **Security First** (P1): .gitignore setup and secret scanning must be complete before any Git operations
2. **Directory Structure** (P1): Domain subdirectories must exist before agents can route tasks
3. **Git Sync** (P2): Basic sync working before claim protocol
4. **Claim Protocol** (P2): Atomic claims working before concurrent agent testing
5. **Watchdog** (P3): Can be added after basic sync and claims are working
6. **Dashboard Manager** (P3): Can be added last as it's an optimization

### Testing Strategy

1. **Unit Tests**: Each module independently testable
   - Git sync operations (mock GitPython)
   - Claim protocol (test atomic moves)
   - Watchdog (test stalled detection)

2. **Integration Tests**: End-to-end scenarios
   - Two agents claiming same task (verify only one succeeds)
   - Agent crash during processing (verify watchdog recovery)
   - Network failure during sync (verify retry logic)
   - Secret file in vault (verify pre-commit hook blocks)

3. **Security Tests**: Audit Git history
   - Verify no .env files in history
   - Verify no credentials/ files in history
   - Verify no *.token files in history

### Rollout Plan

1. **Local Testing**: Test sync between two local vault copies
2. **Remote Testing**: Test sync with GitHub/GitLab private repo
3. **Concurrent Testing**: Run two agents simultaneously, verify no conflicts
4. **Crash Testing**: Kill agent mid-operation, verify watchdog recovery
5. **Production**: Enable for actual Cloud-Local coordination

## Dependencies & Risks

### Internal Dependencies

- ✅ Bronze Tier: Vault structure exists
- ✅ Silver Tier: Watchers and orchestrator functional
- ✅ Gold Tier: Error recovery system operational

### External Dependencies

- Git 2.x+ installed on both Local and Cloud
- GitHub/GitLab private repository created
- SSH keys or HTTPS credentials configured
- Network connectivity for Git operations

### Risks

1. **Secret Leakage** (High Impact, Medium Likelihood)
   - Mitigation: Pre-commit hooks, regular audits, .gitignore validation

2. **Git Merge Conflicts** (Medium Impact, Medium Likelihood)
   - Mitigation: Single-writer rule, domain separation, conflict resolution strategy

3. **Network Outages** (Low Impact, High Likelihood)
   - Mitigation: Local operation continues, retry with backoff, manual sync command

4. **Vault Size Growth** (Medium Impact, Medium Likelihood)
   - Mitigation: Archive old tasks, log rotation, size monitoring

## Next Steps

1. Run `/sp.tasks` to generate implementation task breakdown
2. Execute Phase 0 research (create research.md)
3. Execute Phase 1 design (create data-model.md, contracts/, quickstart.md)
4. Begin implementation following task priorities
