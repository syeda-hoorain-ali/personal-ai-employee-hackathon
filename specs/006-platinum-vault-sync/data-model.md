# Data Model: Platinum Tier Phase 1A - Vault Sync Infrastructure

**Feature**: 006-platinum-vault-sync
**Date**: 2026-02-22
**Purpose**: Define data structures and formats for vault synchronization

## 1. Task File Format

### Structure

Task files are markdown documents with YAML frontmatter containing metadata.

```yaml
---
id: task-20260222-103000-email-001
domain: email | social | local-only
priority: high | medium | low
created: 2026-02-22T10:30:00Z
claimed_by: cloud-agent | local-agent | null
claimed_at: 2026-02-22T10:35:00Z | null
status: pending | in_progress | completed
source: gmail_watcher | filesystem_watcher | manual
metadata:
  email_id: msg-12345  # Optional: source-specific metadata
  thread_id: thread-67890
---

# Task: Triage Email from John Doe

## Context
Email received from john.doe@example.com regarding project update.

## Required Action
- Read email content
- Categorize as urgent/normal/low priority
- Draft reply if needed
- Move to appropriate folder

## Notes
- Previous conversation context in thread-67890
- User prefers brief responses to project updates
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier: `task-{timestamp}-{domain}-{sequence}` |
| `domain` | enum | Yes | Work category: `email`, `social`, `local-only` |
| `priority` | enum | Yes | Task urgency: `high`, `medium`, `low` |
| `created` | ISO8601 | Yes | Task creation timestamp (UTC) |
| `claimed_by` | string | No | Agent name that claimed task, null if unclaimed |
| `claimed_at` | ISO8601 | No | Claim timestamp (UTC), null if unclaimed |
| `status` | enum | Yes | Current state: `pending`, `in_progress`, `completed` |
| `source` | string | Yes | Origin: `gmail_watcher`, `filesystem_watcher`, `manual` |
| `metadata` | object | No | Source-specific additional data |

### File Naming Convention

- **Pattern**: `{timestamp}-{domain}-{sequence}.md`
- **Example**: `20260222-103000-email-001.md`
- **Rationale**: Sortable by time, domain visible, unique sequence prevents collisions

### Lifecycle States

```
pending → in_progress → completed
   ↓           ↓
   └─────── (stalled) ──→ pending (watchdog recovery)
```

---

## 2. Domain Configuration

### Structure

Domain configuration defines which agents can access which work categories.

```yaml
# File: AI_Employee_Vault/.config/domains.yaml

domains:
  email:
    description: "Email triage, drafting, and sending"
    cloud_access: true
    local_access: true
    requires_approval: true
    approval_threshold: all  # all | high_priority | none

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
    can_send: false  # Requires Local approval

  local-agent:
    allowed_domains:
      - email
      - social
      - local-only
    can_draft: true
    can_send: true  # Can execute final actions
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | Human-readable domain purpose |
| `cloud_access` | boolean | Can Cloud agent process tasks in this domain? |
| `local_access` | boolean | Can Local agent process tasks in this domain? |
| `requires_approval` | boolean | Must drafts be approved before execution? |
| `approval_threshold` | enum | When approval needed: `all`, `high_priority`, `none` |

### Agent Configuration

| Field | Type | Description |
|-------|------|-------------|
| `allowed_domains` | list[string] | Domains this agent can access |
| `can_draft` | boolean | Can create draft content (replies, posts) |
| `can_send` | boolean | Can execute final actions (send email, post) |

---

## 3. Agent Claim State

### Representation

Agent claims are represented by **file location** in the filesystem. No separate state file needed.

```
Needs_Action/email/task-001.md     → Unclaimed (available)
In_Progress/cloud-agent/task-001.md → Claimed by cloud-agent
In_Progress/local-agent/task-002.md → Claimed by local-agent
Done/email/task-001-20260222.md     → Completed
```

### Claim Metadata

Claim information is stored in the task file's YAML frontmatter:

```yaml
claimed_by: cloud-agent
claimed_at: 2026-02-22T10:35:00Z
```

### Claim Validation Rules

1. **Atomic Move**: Task moves from `Needs_Action/` to `In_Progress/` in single operation
2. **Unique Claim**: Only one agent can claim a task (enforced by filesystem)
3. **Timeout**: Claims expire after 30 minutes of inactivity (watchdog recovery)
4. **Domain Check**: Agent must have access to task's domain

---

## 4. Cloud Status Update Format

### Structure

Cloud agent writes status updates to `Updates/` directory for Local agent to merge.

```yaml
---
timestamp: 2026-02-22T10:40:00Z
agent: cloud-agent
type: status | approval_request | notification | error
priority: high | medium | low
related_task: task-20260222-103000-email-001  # Optional
---

# Status Update: Email Triage Complete

## Summary
Processed 5 emails from inbox. 3 require replies, 2 archived.

## Pending Approvals
- **task-001**: Reply to John Doe (project update)
- **task-002**: Reply to Jane Smith (meeting request)
- **task-003**: Reply to Bob Johnson (invoice question)

## Actions Taken
- Archived 2 newsletters
- Categorized 3 emails as requiring response

## Next Steps
Awaiting Local agent approval for draft replies in `Pending_Approval/email/`.
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `timestamp` | ISO8601 | Yes | Update creation time (UTC) |
| `agent` | string | Yes | Agent name: `cloud-agent` |
| `type` | enum | Yes | Update category: `status`, `approval_request`, `notification`, `error` |
| `priority` | enum | Yes | Update urgency: `high`, `medium`, `low` |
| `related_task` | string | No | Task ID if update relates to specific task |

### File Naming Convention

- **Pattern**: `cloud-status-{timestamp}.md`
- **Example**: `cloud-status-20260222-104000.md`
- **Location**: `Updates/cloud-status-{timestamp}.md`

### Update Types

| Type | Purpose | Example |
|------|---------|---------|
| `status` | General progress report | "Processed 10 emails" |
| `approval_request` | Needs Local approval | "Draft reply ready for review" |
| `notification` | Important alert | "High priority email detected" |
| `error` | Problem encountered | "Failed to access Gmail API" |

---

## 5. Vault State Representation

### Directory Structure

```
AI_Employee_Vault/
├── .config/
│   └── domains.yaml              # Domain configuration
│
├── Needs_Action/
│   ├── email/                    # Unclaimed email tasks
│   │   └── task-001.md
│   ├── social/                   # Unclaimed social tasks
│   │   └── task-002.md
│   └── local-only/               # Unclaimed local-only tasks
│       └── task-003.md
│
├── In_Progress/
│   ├── cloud-agent/              # Cloud-claimed tasks
│   │   └── task-001.md
│   └── local-agent/              # Local-claimed tasks
│       └── task-003.md
│
├── Pending_Approval/
│   ├── email/                    # Email drafts awaiting approval
│   │   └── draft-reply-001.md
│   └── social/                   # Social post drafts awaiting approval
│       └── draft-post-001.md
│
├── Updates/
│   ├── cloud-status-20260222-104000.md
│   └── archive/                  # Processed updates
│       └── cloud-status-20260222-103000.md
│
├── Done/
│   ├── email/                    # Completed email tasks
│   │   └── task-001-20260222.md
│   ├── social/                   # Completed social tasks
│   │   └── task-002-20260222.md
│   └── local-only/               # Completed local-only tasks
│       └── task-003-20260222.md
│
├── Dashboard.md                  # Local agent writes only
├── Company_Handbook.md           # User edits only
└── Business_Goals.md             # User edits only
```

### State Transitions

```
1. Task Creation:
   Watcher → Needs_Action/{domain}/task.md

2. Task Claiming:
   Needs_Action/{domain}/task.md → In_Progress/{agent}/task.md

3. Task Completion:
   In_Progress/{agent}/task.md → Done/{domain}/task-{timestamp}.md

4. Stalled Recovery:
   In_Progress/{agent}/task.md → Needs_Action/{domain}/task.md

5. Approval Flow:
   In_Progress/{agent}/task.md → Pending_Approval/{domain}/draft.md
   Pending_Approval/{domain}/draft.md → (approved) → Done/{domain}/task.md
   Pending_Approval/{domain}/draft.md → (rejected) → Needs_Action/{domain}/task.md
```

---

## 6. Git Commit Message Format

### Convention

```
[{agent-name}] {action} {domain}: {description}

Examples:
[cloud-agent] claim email: Triage inbox (5 emails)
[cloud-agent] draft email: Reply to John Doe re: project update
[local-agent] approve email: Send reply to John Doe
[local-agent] complete local-only: Process payment to vendor
[watchdog] recover email: Move stalled task-001 back to Needs_Action
```

### Format Rules

| Component | Description | Example |
|-----------|-------------|---------|
| `agent-name` | Agent or system component | `cloud-agent`, `local-agent`, `watchdog` |
| `action` | Operation performed | `claim`, `draft`, `approve`, `complete`, `recover` |
| `domain` | Work category | `email`, `social`, `local-only` |
| `description` | Brief summary | `Triage inbox (5 emails)` |

### Rationale

- **Searchable**: Easy to filter commits by agent, action, or domain
- **Auditable**: Clear trail of who did what
- **Readable**: Git log tells story of agent operations

---

## 7. Validation Rules

### Task File Validation

```python
def validate_task_file(task_file: Path) -> bool:
    """Validate task file structure and content."""
    # Parse YAML frontmatter
    frontmatter = parse_yaml_frontmatter(task_file)

    # Required fields present
    required = ['id', 'domain', 'priority', 'created', 'status', 'source']
    if not all(field in frontmatter for field in required):
        return False

    # Domain is valid
    if frontmatter['domain'] not in ['email', 'social', 'local-only']:
        return False

    # Priority is valid
    if frontmatter['priority'] not in ['high', 'medium', 'low']:
        return False

    # Status is valid
    if frontmatter['status'] not in ['pending', 'in_progress', 'completed']:
        return False

    # Timestamps are ISO8601
    try:
        datetime.fromisoformat(frontmatter['created'])
        if frontmatter.get('claimed_at'):
            datetime.fromisoformat(frontmatter['claimed_at'])
    except ValueError:
        return False

    return True
```

### Domain Access Validation

```python
def validate_domain_access(agent_name: str, domain: str) -> bool:
    """Check if agent has access to domain."""
    config = load_domain_config()
    agent_config = config['agent_config'][agent_name]

    return domain in agent_config['allowed_domains']
```

---

## 8. Performance Considerations

### File Size Limits

- **Task files**: Max 100 KB (typical: 1-5 KB)
- **Status updates**: Max 50 KB (typical: 1-2 KB)
- **Dashboard.md**: Max 500 KB (typical: 10-50 KB)

### Directory Limits

- **Needs_Action/**: Max 1,000 tasks per domain (archive if exceeded)
- **In_Progress/**: Max 100 tasks per agent (watchdog recovery if exceeded)
- **Updates/**: Max 100 unprocessed updates (archive older than 24 hours)
- **Done/**: Unlimited (archive to separate repo monthly)

### Git Performance

- **Vault size**: Target <100 MB (archive old tasks if exceeded)
- **File count**: Target <10,000 files (Git performance degrades beyond this)
- **Commit frequency**: Max 1 commit per minute per agent (batch operations)

---

## Summary

This data model provides:
- ✅ Clear task file format with metadata
- ✅ Domain-based access control
- ✅ File-location-based claim state (no separate DB)
- ✅ Cloud status update format for Local merging
- ✅ Git commit message convention for auditability
- ✅ Validation rules for data integrity
- ✅ Performance limits for scalability

All data structures are file-based, human-readable (markdown/YAML), and Git-friendly.
