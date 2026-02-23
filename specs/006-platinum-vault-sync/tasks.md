# Tasks: Platinum Tier Phase 1A - Vault Sync Infrastructure

**Input**: Design documents from `/specs/006-platinum-vault-sync/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not requested in specification - focusing on implementation only

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- Python code: `app/src/app/`
- Vault: `AI_Employee_Vault/`
- Tests: `tests/`
- Config: `.gitignore`, `.pre-commit-config.yaml`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency installation

- [X] T001 Install GitPython 3.1+ dependency via pip or uv
- [X] T002 [P] Install watchdog 3.0+ dependency via pip or uv
- [X] T003 [P] Install pre-commit 3.5+ dependency via pip or uv
- [X] T004 Create base module structure: app/src/app/vault_sync/__init__.py
- [X] T005 [P] Create base module structure: app/src/app/domain_manager/__init__.py
- [X] T006 [P] Create base module structure: app/src/app/claim_protocol/__init__.py
- [X] T007 [P] Create base module structure: app/src/app/watchdog/__init__.py
- [X] T008 [P] Create base module structure: app/src/app/dashboard_manager/__init__.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T009 Initialize Git repository in AI_Employee_Vault/ if not already present
- [ ] T010 Create GitHub/GitLab private repository for vault sync
- [ ] T011 Configure Git remote origin for AI_Employee_Vault/
- [X] T012 Create base vault directory structure: AI_Employee_Vault/.config/
- [X] T013 [P] Create environment variable template: .env.example with AGENT_NAME, VAULT_PATH, GIT_SYNC_ENABLED
- [X] T014 [P] Add vault sync configuration to existing logging_config.py for structured logging

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Secure Vault Synchronization (Priority: P1) 🎯 MVP

**Goal**: Synchronize vault between Cloud and Local while ensuring secrets never leave local machine

**Independent Test**: Set up Git sync, add test secret file (.env.test), commit and push, pull on separate machine, verify secret excluded while markdown files synced

### Implementation for User Story 1

- [X] T015 [P] [US1] Update .gitignore to exclude .env, .env.*, credentials/, sessions/, *.token, *.key, *.pem, gmail_credentials.json, token.pickle
- [X] T016 [P] [US1] Create .pre-commit-config.yaml with detect-secrets hook configuration
- [X] T017 [US1] Install pre-commit hooks by running pre-commit install in AI_Employee_Vault/
- [X] T018 [US1] Create initial secrets baseline: detect-secrets scan > .secrets.baseline in AI_Employee_Vault/
- [X] T019 [P] [US1] Implement GitManager class in app/src/app/vault_sync/git_manager.py with sync_vault(), pull_changes(), push_changes() methods
- [X] T020 [P] [US1] Implement ConflictResolver class in app/src/app/vault_sync/conflict_resolver.py with resolve_conflict() method
- [X] T021 [P] [US1] Implement SecretScanner class in app/src/app/vault_sync/secret_scanner.py with scan_for_secrets() method
- [X] T022 [US1] Add retry logic with exponential backoff to GitManager for network failures
- [X] T023 [US1] Add Git commit message formatting: [agent-name] action domain: description in GitManager
- [X] T024 [US1] Integrate GitManager with existing orchestrator.py to add sync cycle hooks
- [X] T025 [US1] Add error recovery integration: use existing error_recovery module for Git sync failures
- [X] T026 [US1] Create .gitattributes in AI_Employee_Vault/ to disable delta compression for markdown files
- [X] T027 [US1] Test secret exclusion: create test .env file, verify not tracked by Git, verify not in Git history

**Checkpoint**: At this point, User Story 1 should be fully functional - vault syncs securely with zero secrets in Git

---

## Phase 4: User Story 2 - Domain-Based Work Separation (Priority: P2)

**Goal**: Organize vault into domain-specific directories so agents have clear ownership boundaries

**Independent Test**: Create test task files in different domain directories, verify agents only process authorized domains

### Implementation for User Story 2

- [X] T028 [P] [US2] Create domain subdirectories: AI_Employee_Vault/Needs_Action/email/
- [X] T029 [P] [US2] Create domain subdirectories: AI_Employee_Vault/Needs_Action/social/
- [X] T030 [P] [US2] Create domain subdirectories: AI_Employee_Vault/Needs_Action/local-only/
- [X] T031 [P] [US2] Create approval subdirectories: AI_Employee_Vault/Pending_Approval/email/
- [X] T032 [P] [US2] Create approval subdirectories: AI_Employee_Vault/Pending_Approval/social/
- [X] T033 [P] [US2] Create progress subdirectories: AI_Employee_Vault/In_Progress/cloud-agent/
- [X] T034 [P] [US2] Create progress subdirectories: AI_Employee_Vault/In_Progress/local-agent/
- [X] T035 [P] [US2] Create done subdirectories: AI_Employee_Vault/Done/email/, Done/social/, Done/local-only/
- [X] T036 [P] [US2] Create updates directory: AI_Employee_Vault/Updates/ and Updates/archive/
- [X] T037 [P] [US2] Create .gitkeep files in all new directories to track empty directories in Git
- [X] T038 [US2] Create domain configuration file: AI_Employee_Vault/.config/domains.yaml with email, social, local-only domain definitions
- [X] T039 [US2] Implement DomainConfig class in app/src/app/domain_manager/domain_config.py to load and parse domains.yaml
- [X] T040 [US2] Implement DomainRouter class in app/src/app/domain_manager/domain_router.py with can_access_domain() and get_allowed_domains() methods
- [X] T041 [US2] Integrate DomainRouter with existing file_processor.py to filter tasks by agent's allowed domains
- [X] T042 [US2] Add domain validation to task file YAML frontmatter parsing in vault_reader.py
- [X] T043 [US2] Test domain access: create test tasks in email/ and local-only/, verify cloud-agent can only access email/

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - vault syncs securely AND agents respect domain boundaries

---

## Phase 5: User Story 3 - Conflict-Free Task Claiming (Priority: P3)

**Goal**: Agents use claim-by-move protocol so they never duplicate work or process same task simultaneously

**Independent Test**: Run two agent instances simultaneously, place task in Needs_Action/email/, verify only one agent moves it to In_Progress/

### Implementation for User Story 3

- [X] T044 [P] [US3] Implement ClaimManager class in app/src/app/claim_protocol/claim_manager.py with claim_task(), release_task(), complete_task() methods using os.replace()
- [X] T045 [P] [US3] Implement ClaimValidator class in app/src/app/claim_protocol/claim_validator.py with validate_claim() and is_claimed() methods
- [X] T046 [US3] Add atomic file move logic with pre-check pattern to ClaimManager.claim_task()
- [X] T047 [US3] Add claim timeout configuration: read CLAIM_TIMEOUT_MINUTES from environment variables (default 30)
- [X] T048 [US3] Update task file YAML frontmatter to include claimed_by and claimed_at fields when claiming
- [X] T049 [US3] Integrate ClaimManager with existing file_processor.py to claim tasks before processing
- [X] T050 [P] [US3] Implement TaskWatchdog class in app/src/app/watchdog/task_watchdog.py with check_stalled_tasks() method
- [X] T051 [P] [US3] Implement RecoveryHandler class in app/src/app/watchdog/recovery_handler.py with recover_stalled_task() method
- [X] T052 [US3] Add watchdog polling loop: check In_Progress/ every 5 minutes for tasks with no updates for 30+ minutes
- [X] T053 [US3] Add watchdog recovery: move stalled tasks from In_Progress/ back to Needs_Action/<domain>/
- [X] T054 [US3] Integrate TaskWatchdog with orchestrator.py to run as separate thread
- [X] T055 [US3] Add watchdog configuration: read WATCHDOG_ENABLED and WATCHDOG_INTERVAL_SECONDS from environment variables
- [X] T056 [US3] Test concurrent claims: run two agents simultaneously, verify only one claims task, other skips

**Checkpoint**: All user stories 1-3 should now be independently functional - secure sync, domain separation, AND conflict-free claiming

---

## Phase 6: User Story 4 - Dashboard Single-Writer Rule (Priority: P3)

**Goal**: Local agent is sole writer of Dashboard.md while Cloud writes to Updates/, preventing merge conflicts

**Independent Test**: Cloud agent writes status to Updates/, Local agent merges into Dashboard.md, verify no Git conflicts

### Implementation for User Story 4

- [X] T057 [P] [US4] Implement CloudUpdateWriter class in app/src/app/dashboard_manager/cloud_update_writer.py with write_status_update() method
- [X] T058 [P] [US4] Implement UpdateMerger class in app/src/app/dashboard_manager/update_merger.py with merge_updates_to_dashboard() method
- [X] T059 [US4] Add timestamp-based filename generation for cloud status updates: Updates/cloud-status-{timestamp}.md
- [X] T060 [US4] Add YAML frontmatter to cloud status updates: timestamp, agent, type, priority, related_task
- [X] T061 [US4] Implement update merger logic: read Updates/*.md files, extract key info, append to Dashboard.md
- [X] T062 [US4] Add update archiving: move processed updates from Updates/ to Updates/archive/ after merging
- [X] T063 [US4] Add agent-specific Dashboard.md write restriction: only local-agent can write, cloud-agent uses CloudUpdateWriter
- [X] T064 [US4] Integrate CloudUpdateWriter with orchestrator.py for cloud-agent status reporting
- [X] T065 [US4] Integrate UpdateMerger with orchestrator.py for local-agent periodic merging
- [X] T066 [US4] Add merge frequency configuration: read DASHBOARD_MERGE_INTERVAL_SECONDS from environment variables (default 300)
- [X] T067 [US4] Test single-writer rule: run both agents concurrently, verify no Git conflicts on Dashboard.md

**Checkpoint**: All user stories should now be independently functional - complete Platinum Phase 1A infrastructure

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T068 [P] Add comprehensive logging for all vault sync operations using existing logging_config.py
- [X] T069 [P] Add performance monitoring: track sync duration, claim duration, watchdog scan duration
- [X] T070 [P] Create setup script: scripts/setup_vault_sync.sh to automate Steps 1-11 from quickstart.md
- [X] T071 [P] Update README.md with Platinum Phase 1A completion status and setup instructions
- [X] T072 [P] Add error handling for all Git operations: network failures, authentication errors, merge conflicts
- [X] T073 [P] Add validation for task file YAML frontmatter: required fields, valid domains, valid priorities
- [X] T074 [P] Add Git history audit script: scripts/audit_git_secrets.sh using truffleHog
- [X] T075 Run quickstart.md validation: execute all 12 steps, verify vault sync works end-to-end
- [X] T076 Create troubleshooting documentation: docs/platinum-vault-sync-troubleshooting.md
- [X] T077 Security audit: verify zero secrets in Git history, verify .gitignore works, verify pre-commit hooks block secrets

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P3)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories (independent)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Integrates with US2 (domain directories) but independently testable
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - No dependencies on other stories (independent)

### Within Each User Story

- US1: .gitignore and pre-commit setup → GitManager → Integration with orchestrator
- US2: Directory creation → Domain config → Domain router → Integration with file processor
- US3: ClaimManager → Watchdog → Integration with orchestrator
- US4: CloudUpdateWriter and UpdateMerger → Integration with orchestrator

### Parallel Opportunities

- **Setup (Phase 1)**: T002, T003, T005, T006, T007, T008 can run in parallel
- **Foundational (Phase 2)**: T013, T014 can run in parallel
- **User Story 1**: T015, T016, T019, T020, T021 can run in parallel (different files)
- **User Story 2**: T028-T037 (directory creation) can run in parallel, T039-T040 can run in parallel
- **User Story 3**: T044, T045, T050, T051 can run in parallel (different files)
- **User Story 4**: T057, T058 can run in parallel (different files)
- **Polish (Phase 7)**: T068, T069, T070, T071, T072, T073, T074 can run in parallel
- **All user stories (Phase 3-6)** can be worked on in parallel by different team members after Foundational phase completes

---

## Parallel Example: User Story 1

```bash
# Launch all parallelizable tasks for User Story 1 together:
Task T015: "Update .gitignore to exclude secrets"
Task T016: "Create .pre-commit-config.yaml"
Task T019: "Implement GitManager class"
Task T020: "Implement ConflictResolver class"
Task T021: "Implement SecretScanner class"

# These can all be worked on simultaneously as they modify different files
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T008)
2. Complete Phase 2: Foundational (T009-T014) - CRITICAL
3. Complete Phase 3: User Story 1 (T015-T027)
4. **STOP and VALIDATE**: Test User Story 1 independently
   - Create test secret file, verify excluded from Git
   - Create test markdown file, verify synced to remote
   - Verify Git history has zero secrets
5. Deploy/demo if ready - **This is your MVP!**

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP - secure sync!)
3. Add User Story 2 → Test independently → Deploy/Demo (+ domain separation)
4. Add User Story 3 → Test independently → Deploy/Demo (+ conflict-free claiming)
5. Add User Story 4 → Test independently → Deploy/Demo (+ single-writer Dashboard)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T014)
2. Once Foundational is done:
   - Developer A: User Story 1 (T015-T027) - Secure sync
   - Developer B: User Story 2 (T028-T043) - Domain separation
   - Developer C: User Story 3 (T044-T056) - Claim protocol
   - Developer D: User Story 4 (T057-T067) - Dashboard manager
3. Stories complete and integrate independently
4. Team completes Polish together (T068-T077)

---

## Task Summary

**Total Tasks**: 77
- Setup: 8 tasks
- Foundational: 6 tasks (BLOCKING)
- User Story 1 (P1): 13 tasks - Secure Vault Synchronization
- User Story 2 (P2): 16 tasks - Domain-Based Work Separation
- User Story 3 (P3): 13 tasks - Conflict-Free Task Claiming
- User Story 4 (P3): 11 tasks - Dashboard Single-Writer Rule
- Polish: 10 tasks

**Parallel Opportunities**: 35 tasks marked [P] can run in parallel within their phase

**Independent Test Criteria**:
- US1: Secret file excluded, markdown synced, zero secrets in Git history
- US2: Agents respect domain boundaries, cloud-agent cannot access local-only/
- US3: Only one agent claims task, watchdog recovers stalled tasks
- US4: No Git conflicts on Dashboard.md with concurrent agents

**Suggested MVP Scope**: Phase 1 + Phase 2 + Phase 3 (User Story 1 only) = 27 tasks

---

## Notes

- [P] tasks = different files, no dependencies within phase
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All file paths are exact locations from plan.md
- No tests included (not requested in specification)
- Focus on implementation and integration with existing codebase
