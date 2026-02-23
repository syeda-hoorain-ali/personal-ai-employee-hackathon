# Research & Technical Decisions

**Feature**: 006-platinum-vault-sync
**Date**: 2026-02-22
**Purpose**: Resolve technical unknowns and document architectural decisions

## 1. GitPython Atomic Operations

### Research Question
How to implement atomic commit/push/pull cycles with GitPython while handling network failures and optimizing performance for large repos?

### Decision: Periodic Batch Sync with Retry Logic

**Chosen Approach**: Sync after each agent operation cycle (not per-file) with exponential backoff retry

**Rationale**:
- Reduces Git overhead (1 commit per cycle vs. 100+ commits per cycle)
- Maintains reasonable sync freshness (agents sync every 2-5 minutes)
- Network failures don't block agent operations (async retry)
- Git history remains readable (meaningful commits, not noise)

**Implementation Pattern**:
```python
# Sync cycle: pull → work → commit → push
try:
    repo.remotes.origin.pull(rebase=True)  # Rebase to avoid merge commits
    # Agent does work...
    repo.index.add(['*.md', '*.json'])  # Stage only tracked file types
    repo.index.commit(f"[{agent_name}] {action} {domain}: {description}")
    repo.remotes.origin.push()
except GitCommandError as e:
    # Log error, queue for retry with exponential backoff
    retry_queue.add(sync_operation, backoff=2**attempt)
```

**Performance Optimization**:
- Use `.gitattributes` to disable delta compression for markdown (faster commits)
- Shallow clone for Cloud agent (only recent history needed)
- Git GC scheduled weekly to maintain performance

**Alternatives Considered**:
- ❌ Sync per file: Too much overhead, unreadable Git history
- ❌ Manual sync only: Risk of divergence, requires user intervention
- ❌ Real-time sync: Complex, requires WebSocket/polling, out of scope

---

## 2. File-Based Claim Protocol

### Research Question
How to implement atomic file moves for task claiming that prevents race conditions across platforms?

### Decision: os.replace() with Pre-Check Pattern

**Chosen Approach**: Use `os.replace()` for atomic moves with existence pre-check

**Rationale**:
- `os.replace()` is atomic on both Windows and Linux (POSIX rename semantics)
- Pre-check prevents unnecessary exceptions in common case
- Filesystem is source of truth (no separate lock files needed)
- Cross-platform compatible (tested on Windows 10, Linux)

**Implementation Pattern**:
```python
def claim_task(task_path: Path, agent_name: str) -> bool:
    """Atomically claim a task by moving it to In_Progress."""
    claim_path = Path(f"In_Progress/{agent_name}/{task_path.name}")

    # Pre-check: Is task still available?
    if not task_path.exists():
        return False  # Already claimed by another agent

    # Pre-check: Is claim destination already occupied?
    if claim_path.exists():
        return False  # Duplicate claim attempt

    try:
        # Atomic move (fails if source disappeared between check and move)
        os.replace(str(task_path), str(claim_path))
        return True
    except FileNotFoundError:
        # Race condition: another agent claimed between check and move
        return False
```

**Claim Timeout**: 30 minutes (configurable via environment variable)
- Reasonable for most tasks (email triage, social posts)
- Watchdog checks every 5 minutes, moves stalled tasks after 30 minutes
- Configurable for long-running tasks (set CLAIM_TIMEOUT_MINUTES)

**Alternatives Considered**:
- ❌ `shutil.move()`: Not atomic on Windows (copy + delete)
- ❌ File locking (fcntl/msvcrt): Complex, platform-specific, requires lock cleanup
- ❌ Database for claims: Adds dependency, requires sync with filesystem

---

## 3. Git Conflict Resolution

### Research Question
How to handle merge conflicts when both agents modify files concurrently?

### Decision: Single-Writer Rule + Conflict Detection

**Chosen Approach**: Prevent conflicts via single-writer rules, detect and alert on unavoidable conflicts

**Conflict Prevention**:
1. **Dashboard.md**: Local agent is exclusive writer
   - Cloud writes to `Updates/cloud-status-[timestamp].md`
   - Local merges updates into Dashboard.md
   - Zero conflicts by design

2. **Task Files**: Domain separation + claim-by-move
   - Each task file owned by one agent at a time (via In_Progress/)
   - Different domains rarely overlap
   - Conflicts only if both agents modify same unclaimed task

3. **Configuration Files**: Manual edit only (not agent-modified)
   - Company_Handbook.md, Business_Goals.md edited by user
   - Agents read-only for these files

**Conflict Detection & Resolution**:
```python
def sync_with_conflict_detection():
    try:
        repo.remotes.origin.pull(rebase=True)
    except GitCommandError as e:
        if "CONFLICT" in str(e):
            conflicts = repo.index.unmerged_blobs()

            # Dashboard.md conflict: Local wins (should never happen)
            if "Dashboard.md" in conflicts:
                repo.git.checkout("--ours", "Dashboard.md")
                log_error("Dashboard conflict detected - Local wins")

            # Other conflicts: Alert user for manual review
            else:
                log_error(f"Merge conflict requires manual review: {conflicts}")
                notify_user(conflicts)
                # Agent pauses until conflict resolved
```

**Alternatives Considered**:
- ❌ Automatic merge strategies (ours/theirs): Risk of data loss
- ❌ Operational Transform (OT): Too complex for file-based system
- ❌ Last-write-wins: Risk of losing work

---

## 4. Secret Scanning

### Research Question
Which secret scanning approach prevents credential leakage most effectively?

### Decision: pre-commit Framework with detect-secrets

**Chosen Approach**: Use `pre-commit` framework with `detect-secrets` plugin

**Rationale**:
- `pre-commit` is standard Python tool (widely adopted, well-maintained)
- `detect-secrets` uses entropy-based detection (catches unknown secret types)
- Blocks commits before they enter Git history (prevention vs. detection)
- Configurable baseline for false positives
- Works on both Local and Cloud environments

**Configuration** (`.pre-commit-config.yaml`):
```yaml
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
```

**Secret Patterns to Detect**:
- High entropy strings (API keys, tokens)
- AWS keys, GitHub tokens, private keys
- Passwords in configuration files
- Email addresses in credentials

**Baseline Management**:
- Initial scan creates `.secrets.baseline` with known false positives
- Developers audit baseline, mark legitimate secrets
- CI/CD fails if new secrets detected without baseline update

**Git History Scanning**: One-time audit with `truffleHog`
```bash
# Scan entire Git history for secrets
trufflehog git file://. --only-verified --json > secret-audit.json
```

**Alternatives Considered**:
- ❌ `git-secrets`: AWS-focused, misses generic secrets
- ❌ `gitleaks`: Good but less Python ecosystem integration
- ❌ Regex-only: Misses high-entropy secrets, many false positives

---

## 5. Watchdog Implementation

### Research Question
How to efficiently detect and recover stalled tasks without excessive overhead?

### Decision: Polling-Based Watchdog with 5-Minute Intervals

**Chosen Approach**: Separate watchdog process that polls `In_Progress/` every 5 minutes

**Rationale**:
- Simple implementation (no filesystem event complexity)
- Low overhead (5-minute interval acceptable for 30-minute timeout)
- Reliable across platforms (no inotify/FSEvents differences)
- Easy to test (deterministic polling vs. event-driven)

**Implementation Pattern**:
```python
class TaskWatchdog:
    def __init__(self, vault_path: Path, timeout_minutes: int = 30):
        self.vault_path = vault_path
        self.timeout = timedelta(minutes=timeout_minutes)
        self.check_interval = 300  # 5 minutes

    def check_stalled_tasks(self):
        """Scan In_Progress/ for tasks with no updates for 30+ minutes."""
        now = datetime.now()
        in_progress = self.vault_path / "In_Progress"

        for agent_dir in in_progress.iterdir():
            for task_file in agent_dir.glob("*.md"):
                last_modified = datetime.fromtimestamp(task_file.stat().st_mtime)

                if now - last_modified > self.timeout:
                    # Task stalled - move back to Needs_Action
                    domain = self._extract_domain(task_file)
                    recovery_path = self.vault_path / f"Needs_Action/{domain}/{task_file.name}"

                    os.replace(str(task_file), str(recovery_path))
                    log_warning(f"Recovered stalled task: {task_file.name}")
```

**Stalled Task Detection**:
- Use file modification time (`st_mtime`) as last activity indicator
- Agents touch task file periodically during long operations
- Timeout: 30 minutes (configurable via CLAIM_TIMEOUT_MINUTES)

**Recovery Strategy**:
- Move stalled task back to `Needs_Action/<domain>/`
- Log recovery event for audit trail
- Notify user if same task stalls repeatedly (3+ times)

**Watchdog Check Interval**: 5 minutes
- Balances responsiveness (detect within 5 min) vs. overhead
- Acceptable delay for 30-minute timeout (detects at 30-35 minutes)
- Configurable via WATCHDOG_INTERVAL_SECONDS

**Alternatives Considered**:
- ❌ `watchdog` library (filesystem events): Overkill for polling use case, platform differences
- ❌ 1-minute interval: Unnecessary overhead for 30-minute timeout
- ❌ Heartbeat files: Adds complexity, requires agent cooperation

---

## Summary of Decisions

| Area | Decision | Key Benefit |
|------|----------|-------------|
| Git Sync | Periodic batch sync with retry | Readable history, resilient to network failures |
| Claim Protocol | os.replace() with pre-check | Atomic, cross-platform, no external locks |
| Conflict Resolution | Single-writer rules + detection | Zero conflicts by design, alerts on exceptions |
| Secret Scanning | pre-commit + detect-secrets | Prevents secrets before Git commit |
| Watchdog | Polling every 5 minutes | Simple, reliable, low overhead |

## Implementation Priority

1. **P1 - Security**: Secret scanning setup (blocks all other work)
2. **P1 - Directory Structure**: Create domain subdirectories
3. **P2 - Git Sync**: Basic sync working (foundation for everything)
4. **P2 - Claim Protocol**: Atomic claims (enables concurrent agents)
5. **P3 - Watchdog**: Stalled task recovery (reliability improvement)
6. **P3 - Dashboard Manager**: Single-writer optimization

## Performance Expectations

- Git sync: <5 seconds for 1,000 files
- Claim operation: <100ms (atomic file move)
- Watchdog scan: <1 second for 100 in-progress tasks
- Secret scan: <2 seconds for typical commit (10-20 files)

## Testing Validation

Each decision will be validated through:
- Unit tests (mock filesystem, Git operations)
- Integration tests (two agents, concurrent claims)
- Performance tests (1,000 file sync, 100 concurrent claims)
- Security tests (secret detection, Git history audit)
