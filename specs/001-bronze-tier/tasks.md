# Tasks: Bronze Tier - Personal AI Employee Foundation

**Feature**: Bronze Tier - Personal AI Employee Foundation | **Branch**: `001-bronze-tier` | **Date**: 2026-01-14

## Dependencies

User Story 2 (File System Watcher) depends on User Story 1 (Obsidian Vault Setup) being completed first, as the watcher needs to monitor the vault directories. User Story 3 (Claude Code Interaction) depends on User Story 1 being completed, as Claude Code needs to interact with the vault structure.

## Parallel Execution Examples

- Tasks T002-T009 (setting up vault directories) can be executed in parallel
- Tasks T015-T017 (implementing watcher components) can be executed in parallel after T014
- Tasks T022-T024 (testing components) can be executed in parallel after their respective implementation tasks

## Implementation Strategy

MVP scope includes User Story 1 (Obsidian Vault Setup) with minimal viable vault structure. Subsequent stories build upon this foundation incrementally, with each user story delivering independently testable functionality.

---

## Phase 1: Setup Tasks

- [X] T001 Initialize project structure using uv init command with src/, scripts/, tests/ directories per implementation plan

## Phase 2: Foundational Tasks

- [X] T002 Create basic AI_Employee_Vault directory structure
- [X] T003 [P] Create /Inbox directory in AI_Employee_Vault
- [X] T004 [P] Create /Needs-Action directory in AI_Employee_Vault
- [X] T005 [P] Create /Done directory in AI_Employee_Vault
- [X] T006 [P] Create /Plans directory in AI_Employee_Vault
- [X] T007 [P] Create /Pending-Approval directory in AI_Employee_Vault
- [X] T008 [P] Create /Approved directory in AI_Employee_Vault
- [X] T009 [P] Create /Rejected directory in AI_Employee_Vault
- [X] T010 [P] Create /Logs directory in AI_Employee_Vault
- [X] T011 [P] Create /Accounting directory in AI_Employee_Vault
- [X] T012 Add Python watchdog library dependency using uv add command
- [X] T013 [P] Create src/watchers/ directory
- [X] T014 Create base_watcher.py with abstract base class in src/watchers/base_watcher.py

## Phase 3: User Story 1 - Obsidian Vault Setup with Dashboard and Handbook (Priority: P1)

Goal: Establish the foundational Obsidian vault structure with Dashboard.md and Company-Handbook.md to create the AI Employee's knowledge base and operational guidelines.

Independent Test: Create the vault structure with required files and verify they contain appropriate content for the AI to reference.

- [X] T015 [US1] Create Dashboard.md file in AI_Employee_Vault with initial content
- [X] T016 [US1] Create Company-Handbook.md file in AI_Employee_Vault with operational guidelines
- [X] T017 [US1] Populate Company-Handbook.md with communication guidelines, financial guidelines, task management rules, escalation procedures, and working hours guidelines

## Phase 4: User Story 2 - File System Watcher for Task Detection (Priority: P2)

Goal: Implement a file system watcher to monitor for new tasks that require Claude Code processing, automatically triggering Claude when new work items appear in the /Needs-Action folder of the Obsidian vault.

Independent Test: Place files in monitored directories and verify the file system watcher detects and processes them appropriately.

- [X] T018 [P] [US2] Implement filesystem_watcher.py extending base watcher in src/watchers/filesystem_watcher.py
- [X] T019 [P] [US2] Implement gmail_watcher.py extending base watcher in src/watchers/gmail_watcher.py
- [X] T020 [US2] Implement orchestrator.py to coordinate watcher activities in src/orchestrator.py
- [X] T021 [US2] Implement retry_handler.py for handling processing failures in src/retry_handler.py
- [X] T022 [US2] Create test_filesystem_watcher.py for integration tests in tests/integration/test_filesystem_watcher.py
- [X] T023 [US2] Implement setup_vault.py script for initializing vault structure in scripts/setup_vault.py
- [X] T024 [US2] Configure the filesystem watcher to monitor /Needs-Action directory for .md files

## Phase 5: User Story 3 - Claude Code Interaction with Obsidian Vault (Priority: P3)

Goal: Enable Claude Code to read from and write to the Obsidian vault, allowing the AI reasoning engine to process tasks and maintain state in the vault.

Independent Test: Have Claude Code read from vault files and write processed results back to designated folders.

- [X] T025 [US3] Implement file reading functionality for Claude Code to access vault files
- [X] T026 [US3] Implement file writing functionality for Claude Code to save processed results
- [X] T027 [US3] Test Claude Code's ability to read from and write to vault directories
- [X] T028 [US3] Implement logic to move processed files from /Needs-Action to /Done directory
- [X] T029 [US3] Implement logic to process files based on rules defined in Company-Handbook.md

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T030 Add proper logging to all components for observability
- [X] T031 Add error handling and validation for file operations
- [-] T032 Create README.md with project overview and setup instructions
- [X] T033 Test complete workflow: add file to /Needs-Action, verify detection, processing, and movement to /Done
- [X] T034 Document the API contract for the file system watcher functionality
- [X] T035 Verify all functional requirements (FR-001 through FR-008) are satisfied
