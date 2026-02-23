# Feature Specification: Platinum Tier Phase 1A - Vault Sync Infrastructure

**Feature Branch**: `006-platinum-vault-sync`
**Created**: 2026-02-22
**Status**: Draft
**Input**: User description: "Implement Platinum Tier Phase 1A: Vault Sync Infrastructure including security boundaries, domain directory structure, claim-by-move protocol, and Git-based vault synchronization for Cloud-Local agent coordination"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Secure Vault Synchronization (Priority: P1)

As a system owner, I need to synchronize the AI Employee vault between Cloud and Local environments while ensuring sensitive credentials never leave the local machine, so that the Cloud agent can draft work while Local agent maintains exclusive access to sensitive operations.

**Why this priority**: This is the foundational security requirement. Without proper secret isolation, the entire Cloud-Local architecture is compromised. This must work before any cloud deployment.

**Independent Test**: Can be fully tested by setting up Git sync, adding a test secret file (e.g., `.env.test`), committing and pushing from Local, then pulling on a separate test machine and verifying the secret file was excluded while markdown files synced successfully.

**Acceptance Scenarios**:

1. **Given** a vault with `.env` file containing API keys, **When** vault is committed and pushed to Git, **Then** `.env` file is excluded from the commit and does not appear in remote repository
2. **Given** a vault with markdown task files in `Needs_Action/`, **When** vault is committed and pushed to Git, **Then** markdown files are included and successfully sync to remote repository
3. **Given** Gmail credentials stored in `credentials/gmail_token.json`, **When** vault is synced via Git, **Then** credentials file is excluded and never appears in Git history
4. **Given** WhatsApp session files in `sessions/` directory, **When** vault is synced, **Then** session files remain local-only and are not tracked by Git

---

### User Story 2 - Domain-Based Work Separation (Priority: P2)

As a system owner, I need the vault organized into domain-specific directories (email, social, local-only) so that Cloud and Local agents have clear ownership boundaries and know which tasks they can process.

**Why this priority**: Enables work-zone specialization required for Platinum tier. Cloud needs to know which tasks it can draft (email, social) vs. which are Local-exclusive (payments, WhatsApp). This is the foundation for agent coordination.

**Independent Test**: Can be tested by creating test task files in different domain directories (`Needs_Action/email/`, `Needs_Action/local-only/`) and verifying agents only process tasks from their authorized domains based on configuration.

**Acceptance Scenarios**:

1. **Given** an email triage task in `Needs_Action/email/`, **When** Cloud agent scans for work, **Then** Cloud agent can see and claim this task
2. **Given** a payment approval task in `Needs_Action/local-only/`, **When** Cloud agent scans for work, **Then** Cloud agent ignores this task (Local-exclusive)
3. **Given** a social post draft in `Pending_Approval/social/`, **When** Local agent checks for approvals, **Then** Local agent can see and approve/reject the draft
4. **Given** tasks in multiple domain directories, **When** agents process work, **Then** each agent only processes tasks from their authorized domains

---

### User Story 3 - Conflict-Free Task Claiming (Priority: P3)

As a system owner, I need agents to use a claim-by-move protocol so that when multiple agents are running, they never duplicate work or process the same task simultaneously.

**Why this priority**: Prevents wasted work and potential conflicts when both Cloud and Local agents are active. Critical for production reliability but can be implemented after basic sync and domain separation are working.

**Independent Test**: Can be tested by running two agent instances simultaneously, placing a task in `Needs_Action/email/`, and verifying only one agent moves it to `In_Progress/` and processes it while the other agent skips it.

**Acceptance Scenarios**:

1. **Given** a task file in `Needs_Action/email/task.md`, **When** Cloud agent claims it, **Then** file is moved to `In_Progress/cloud-agent/task.md` atomically
2. **Given** a task already in `In_Progress/cloud-agent/`, **When** Local agent scans for work, **Then** Local agent skips this task (already claimed)
3. **Given** Cloud agent crashes mid-processing, **When** task remains in `In_Progress/cloud-agent/` for more than timeout period, **Then** watchdog moves it back to `Needs_Action/` for retry
4. **Given** both agents attempt to claim the same task simultaneously, **When** Git sync occurs, **Then** only one agent's claim succeeds (Git merge conflict resolution or first-writer-wins)

---

### User Story 4 - Dashboard Single-Writer Rule (Priority: P3)

As a system owner, I need Local agent to be the sole writer of `Dashboard.md` while Cloud agent writes updates to a separate location, so that there are no merge conflicts on the critical dashboard file.

**Why this priority**: Prevents Git merge conflicts on the most frequently updated file. Important for smooth operation but not blocking for initial sync setup.

**Independent Test**: Can be tested by having Cloud agent write status updates to `Updates/cloud-status.md`, Local agent periodically reading and merging these into `Dashboard.md`, and verifying no Git conflicts occur during concurrent operations.

**Acceptance Scenarios**:

1. **Given** Cloud agent completes email triage, **When** Cloud needs to report status, **Then** Cloud writes to `Updates/cloud-status-[timestamp].md` (not Dashboard.md)
2. **Given** status updates in `Updates/` directory, **When** Local agent runs, **Then** Local agent reads updates and merges relevant info into `Dashboard.md`
3. **Given** both agents running concurrently, **When** both need to update status, **Then** no Git merge conflicts occur on `Dashboard.md`
4. **Given** Cloud agent offline for extended period, **When** Local agent updates Dashboard, **Then** Cloud agent can sync changes without conflicts when it reconnects

---

### Edge Cases

- What happens when Git push fails due to network issues during agent operation?
- How does system handle Git merge conflicts if both agents modify the same task file simultaneously?
- What happens if `.gitignore` is accidentally modified to include secrets?
- How does system recover if an agent crashes while a task is in `In_Progress/`?
- What happens when vault grows very large (10,000+ files) - does Git sync performance degrade?
- How does system handle timezone differences between Cloud and Local agents for timestamp-based operations?
- What happens if Local agent is offline for days and Cloud accumulates many pending approvals?

## Requirements *(mandatory)*

### Functional Requirements

#### Security & Isolation

- **FR-001**: System MUST exclude all files matching `.env`, `.env.*` patterns from Git tracking
- **FR-002**: System MUST exclude entire `credentials/` directory from Git tracking
- **FR-003**: System MUST exclude entire `sessions/` directory from Git tracking
- **FR-004**: System MUST exclude all files matching `*.token`, `*.key`, `*.pem` patterns from Git tracking
- **FR-005**: System MUST exclude `gmail_credentials.json` and `token.pickle` files from Git tracking
- **FR-006**: System MUST include all markdown files (`*.md`) in Git tracking for state synchronization
- **FR-007**: System MUST include all JSON files in vault directories (except credentials) for state synchronization

#### Directory Structure

- **FR-008**: System MUST create `Needs_Action/email/` directory for email triage tasks
- **FR-009**: System MUST create `Needs_Action/social/` directory for social media tasks
- **FR-010**: System MUST create `Needs_Action/local-only/` directory for Local-exclusive tasks
- **FR-011**: System MUST create `Pending_Approval/email/` directory for email draft approvals
- **FR-012**: System MUST create `Pending_Approval/social/` directory for social post draft approvals
- **FR-013**: System MUST create `In_Progress/cloud-agent/` directory for Cloud-claimed tasks
- **FR-014**: System MUST create `In_Progress/local-agent/` directory for Local-claimed tasks
- **FR-015**: System MUST create `Updates/` directory for Cloud agent status updates
- **FR-016**: System MUST create `Done/email/`, `Done/social/`, `Done/local-only/` directories for completed task archives

#### Claim-by-Move Protocol

- **FR-017**: Agents MUST claim tasks by atomically moving files from `Needs_Action/<domain>/` to `In_Progress/<agent>/`
- **FR-018**: Agents MUST ignore tasks already present in any `In_Progress/` directory
- **FR-019**: Agents MUST move completed tasks from `In_Progress/<agent>/` to `Done/<domain>/` with timestamp
- **FR-020**: System MUST provide watchdog mechanism to detect stalled tasks in `In_Progress/` (no updates for 30+ minutes)
- **FR-021**: Watchdog MUST move stalled tasks back to `Needs_Action/<domain>/` for retry

#### Dashboard Management

- **FR-022**: Local agent MUST be the exclusive writer of `Dashboard.md`
- **FR-023**: Cloud agent MUST write status updates to `Updates/cloud-status-[timestamp].md` files
- **FR-024**: Local agent MUST periodically read and merge updates from `Updates/` directory into `Dashboard.md`
- **FR-025**: System MUST archive processed update files from `Updates/` to `Updates/archive/` after merging

#### Git Synchronization

- **FR-026**: System MUST initialize Git repository in vault root if not already present
- **FR-027**: System MUST configure Git remote for vault synchronization
- **FR-028**: System MUST provide commit message convention: `[agent-name] [action] [domain]: [description]`
- **FR-029**: System MUST commit and push vault changes after each agent operation cycle
- **FR-030**: System MUST pull latest changes before each agent operation cycle
- **FR-031**: System MUST handle Git merge conflicts with conflict resolution strategy (Local-wins for Dashboard.md, manual review for others)

### Key Entities

- **Task File**: Markdown file representing work to be done, contains task description, metadata (domain, priority, created timestamp), and current status. Lives in `Needs_Action/`, `In_Progress/`, or `Done/` directories.

- **Domain**: Work category defining ownership boundaries (email, social, local-only). Determines which agent can process tasks.

- **Agent Claim**: Ownership marker represented by task file location in `In_Progress/<agent>/` directory. Indicates which agent is currently processing the task.

- **Status Update**: Markdown file in `Updates/` directory containing Cloud agent's status report, pending approvals, or notifications for Local agent.

- **Vault State**: Complete synchronized state of AI Employee memory, includes all markdown files, task files, plans, and logs. Excludes secrets and credentials.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Vault can be synchronized between two machines via Git with 100% of markdown files syncing and 0% of secret files syncing
- **SC-002**: Two agents running simultaneously can process 10 tasks without any task being processed twice (0% duplication rate)
- **SC-003**: Git sync operations (commit, push, pull) complete in under 5 seconds for vaults with up to 1,000 files
- **SC-004**: System can recover from agent crashes with 100% of in-progress tasks being automatically retried within 30 minutes
- **SC-005**: Dashboard.md experiences zero Git merge conflicts over 100 concurrent agent operation cycles
- **SC-006**: Security audit confirms 0 secret files present in Git history after 1 week of operation

## Scope *(mandatory)*

### In Scope

- Security boundary setup via `.gitignore` configuration
- Domain-based directory structure creation
- Claim-by-move protocol specification and documentation
- Git-based vault synchronization setup
- Dashboard single-writer rule implementation
- Watchdog for stalled task recovery
- Documentation of sync protocol and conflict resolution

### Out of Scope

- Cloud VM deployment (Phase 1B)
- Actual Cloud agent implementation (Phase 1C)
- Work-zone specialization logic in agents (Phase 1C)
- Agent-to-Agent (A2A) direct messaging (Phase 2)
- Platinum demo implementation (Phase 1D)
- WhatsApp integration
- Payment/banking integration
- Real-time synchronization (using periodic Git sync instead)

## Assumptions *(mandatory)*

1. Git is installed and configured on both Local and Cloud environments
2. User has GitHub/GitLab account with private repository for vault sync
3. Network connectivity is available for Git operations (can tolerate temporary outages)
4. Local machine runs agents when user is actively working (not 24/7)
5. Cloud VM will be deployed in Phase 1B (not part of this phase)
6. Vault size remains under 10,000 files for reasonable Git performance
7. Agents run on same timezone or handle timezone conversions independently
8. User reviews and approves Cloud-drafted content before sending (HITL approval)

## Dependencies *(mandatory)*

### Internal Dependencies

- Bronze Tier: Vault directory structure must exist (`Inbox/`, `Done/`, etc.)
- Silver Tier: Watchers and orchestrator must be functional
- Gold Tier: Error recovery system must be operational for handling sync failures

### External Dependencies

- Git version 2.x or higher
- GitHub/GitLab account with private repository access
- Network connectivity for Git push/pull operations
- SSH keys or HTTPS credentials configured for Git authentication

## Risks & Mitigations *(optional)*

### Risk 1: Secret Leakage via Git

**Impact**: High - Credentials exposed in public/private repository
**Likelihood**: Medium - Human error in `.gitignore` configuration
**Mitigation**:
- Automated pre-commit hook to scan for secret patterns
- Regular security audits of Git history
- Use `git-secrets` or similar tools
- Document secret patterns clearly in `.gitignore`

### Risk 2: Git Merge Conflicts

**Impact**: Medium - Agent operations blocked until manual resolution
**Likelihood**: Medium - Concurrent agent operations on same files
**Mitigation**:
- Single-writer rule for Dashboard.md
- Domain separation reduces file overlap
- Conflict resolution strategy documented
- Watchdog detects and alerts on unresolved conflicts

### Risk 3: Network Outages During Sync

**Impact**: Low - Temporary inability to sync, agents continue locally
**Likelihood**: High - Network issues are common
**Mitigation**:
- Agents operate on local vault copy
- Sync failures logged but don't block agent operations
- Automatic retry with exponential backoff
- Manual sync command available for recovery

### Risk 4: Vault Size Growth

**Impact**: Medium - Git performance degrades with large repos
**Likelihood**: Medium - Logs and task history accumulate over time
**Mitigation**:
- Archive old tasks to separate repository
- Implement log rotation
- Monitor vault size and alert at thresholds
- Document cleanup procedures

## Open Questions *(optional)*

None - all requirements are clear for Phase 1A implementation.
