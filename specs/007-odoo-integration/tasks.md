# Odoo Integration - Implementation Tasks

**Feature**: 007-odoo-integration
**Status**: Ready to Start
**Created**: 2026-02-27

---

## Task Overview

Total: 25 tasks across 6 phases
Estimated Time: 27 hours (~4 days)

---

## Phase 1: Setup & Testing (2 hours)

### T1.1: Install Odoo
**Priority**: Critical
**Estimated Time**: 30 minutes
**Status**: Not Started

**Description**: Install Odoo Community Edition (local or cloud)

**Steps**:
1. Follow `guides/ODOO_SETUP_GUIDE.md`
2. Choose installation method:
   - Option A: Local Windows installation
   - Option B: Odoo.com cloud (15-day trial)
3. Complete installation wizard
4. Verify Odoo is accessible in browser

**Acceptance Criteria**:
- [ ] Odoo accessible at URL (local: http://localhost:8069 or cloud URL)
- [ ] Can login to Odoo web interface
- [ ] PostgreSQL database running

**Dependencies**: None

---

### T1.2: Create Odoo Database
**Priority**: Critical
**Estimated Time**: 10 minutes
**Status**: Not Started

**Description**: Create initial Odoo database with business data

**Steps**:
1. Access Odoo database creation screen
2. Set database name: `my_business`
3. Set admin email and password
4. Uncheck "Demo data"
5. Click "Create database"
6. Wait for database creation (2-3 minutes)

**Acceptance Criteria**:
- [ ] Database created successfully
- [ ] Can login with admin credentials
- [ ] Odoo dashboard visible

**Dependencies**: T1.1

---

### T1.3: Install Odoo Apps
**Priority**: Critical
**Estimated Time**: 5 minutes
**Status**: Not Started

**Description**: Install required Odoo applications

**Steps**:
1. Go to Apps menu in Odoo
2. Install: Accounting, Contacts, Invoicing
3. Wait for installation to complete

**Acceptance Criteria**:
- [ ] Accounting app installed
- [ ] Contacts app installed
- [ ] Invoicing app installed
- [ ] All apps accessible from main menu

**Dependencies**: T1.2

---

### T1.4: Generate Odoo API Key
**Priority**: Critical
**Estimated Time**: 5 minutes
**Status**: Not Started

**Description**: Create API key for MCP server authentication

**Steps**:
1. Click profile icon → "My Profile"
2. Go to "Preferences" tab
3. Scroll to "Account Security"
4. Click "New API Key"
5. Description: `MCP Server Access`
6. Copy the generated key immediately
7. Save key securely (password manager)

**Acceptance Criteria**:
- [ ] API key generated
- [ ] API key copied and saved
- [ ] Can access API key when needed

**Dependencies**: T1.3

---

### T1.5: Update Environment Configuration
**Priority**: Critical
**Estimated Time**: 5 minutes
**Status**: Not Started

**Description**: Configure .env file with Odoo credentials

**Steps**:
1. Open `.env` file in project root
2. Update Odoo configuration section:
   ```env
   ODOO_URL=http://localhost:8069  # or your cloud URL
   ODOO_DB=my_business
   ODOO_API_KEY=your_actual_api_key_here
   ODOO_YOLO=read
   ```
3. Save file
4. Verify no syntax errors

**Acceptance Criteria**:
- [ ] ODOO_URL set correctly
- [ ] ODOO_DB matches database name
- [ ] ODOO_API_KEY contains actual key
- [ ] ODOO_YOLO set to "read" for testing

**Dependencies**: T1.4

---

### T1.6: Test MCP Server Installation
**Priority**: Critical
**Estimated Time**: 10 minutes
**Status**: Not Started

**Description**: Verify MCP server can be installed and run

**Steps**:
1. Open PowerShell
2. Run: `uv --version` (verify UV installed)
3. Run: `uvx mcp-server-odoo --help`
4. Verify help text displays

**Acceptance Criteria**:
- [ ] UV package manager installed
- [ ] MCP server installs without errors
- [ ] Help text displays correctly

**Dependencies**: None

---

### T1.7: Test Odoo MCP Connection
**Priority**: Critical
**Estimated Time**: 15 minutes
**Status**: Not Started

**Description**: Verify MCP server can connect to Odoo

**Steps**:
1. Restart Claude Code (to load new .env)
2. Ask Claude: "List all customers in Odoo"
3. Verify Claude uses Odoo MCP tools
4. Check for connection errors
5. If errors, troubleshoot using guide

**Acceptance Criteria**:
- [ ] Claude Code connects to Odoo MCP server
- [ ] Can list customers (even if empty)
- [ ] No authentication errors
- [ ] No connection timeout errors

**Dependencies**: T1.5, T1.6

---

### T1.8: Add Test Data in Odoo
**Priority**: High
**Estimated Time**: 20 minutes
**Status**: Not Started

**Description**: Create sample data for testing skills

**Steps**:
1. In Odoo Contacts app, create 2 test customers:
   - Customer A: "Test Customer Inc" (company)
   - Customer B: "John Doe" (individual)
2. In Odoo Invoicing app, create 1 test product:
   - Name: "Consulting Services"
   - Unit Price: $150.00
3. Create 1 draft invoice for Test Customer Inc
4. Verify data via Claude Code

**Acceptance Criteria**:
- [ ] 2 customers created in Odoo
- [ ] 1 product/service created
- [ ] 1 draft invoice created
- [ ] Can query test data via Claude Code

**Dependencies**: T1.7

---

## Phase 2: Core Skills (10 hours)

### T2.1: Create Invoice Creator Skill Structure
**Priority**: High
**Estimated Time**: 30 minutes
**Status**: Not Started

**Description**: Set up skill directory and SKILL.md file

**Steps**:
1. Create directory: `.claude/skills/odoo-invoice-creator/`
2. Create `SKILL.md` with skill metadata
3. Define skill purpose and triggers
4. Document input/output format

**Acceptance Criteria**:
- [ ] Skill directory created
- [ ] SKILL.md file exists
- [ ] Skill metadata complete
- [ ] Triggers documented

**Dependencies**: T1.8

---

### T2.2: Implement Invoice Data Extraction
**Priority**: High
**Estimated Time**: 1 hour
**Status**: Not Started

**Description**: Extract invoice details from natural language

**Steps**:
1. Parse customer name from request
2. Extract line items (description, quantity, price)
3. Extract payment terms and due date
4. Handle missing information (ask clarifying questions)

**Acceptance Criteria**:
- [ ] Can extract customer name
- [ ] Can extract line items
- [ ] Can extract payment terms
- [ ] Handles missing data gracefully

**Dependencies**: T2.1

---

### T2.3: Implement Customer Search
**Priority**: High
**Estimated Time**: 45 minutes
**Status**: Not Started

**Description**: Search Odoo for existing customer

**Steps**:
1. Use MCP `search_records` tool
2. Search by customer name
3. Handle multiple matches (ask for clarification)
4. Handle no matches (trigger customer creation)

**Acceptance Criteria**:
- [ ] Can search customers by name
- [ ] Handles exact matches
- [ ] Handles multiple matches
- [ ] Handles no matches

**Dependencies**: T2.2

---

### T2.4: Implement Invoice Creation in Odoo
**Priority**: High
**Estimated Time**: 1 hour
**Status**: Not Started

**Description**: Create draft invoice using MCP tools

**Steps**:
1. Use MCP `create_record` tool
2. Create invoice with customer, line items, terms
3. Set invoice to draft status
4. Capture invoice ID and URL

**Acceptance Criteria**:
- [ ] Can create draft invoice in Odoo
- [ ] Invoice has correct customer
- [ ] Invoice has correct line items
- [ ] Invoice ID captured for approval

**Dependencies**: T2.3

---

### T2.5: Implement Approval File Generation
**Priority**: High
**Estimated Time**: 45 minutes
**Status**: Not Started

**Description**: Generate approval file for invoice

**Steps**:
1. Format invoice data as markdown table
2. Include customer, amount, line items
3. Add Odoo invoice link
4. Write to `Pending_Approval/accounting/`
5. Use naming: `INVOICE_<customer>_<date>.md`

**Acceptance Criteria**:
- [ ] Approval file created
- [ ] Contains all invoice details
- [ ] Formatted as readable markdown
- [ ] Includes Odoo link

**Dependencies**: T2.4

---

### T2.6: Implement Invoice Posting After Approval
**Priority**: High
**Estimated Time**: 45 minutes
**Status**: Not Started

**Description**: Post invoice and send email after approval

**Steps**:
1. Monitor `Approved/accounting/` directory
2. Extract invoice ID from approval file
3. Use MCP `update_record` to post invoice
4. Trigger email send in Odoo
5. Log operation
6. Move task to `Done/accounting/`

**Acceptance Criteria**:
- [ ] Detects approved invoices
- [ ] Posts invoice in Odoo
- [ ] Sends invoice via email
- [ ] Logs operation
- [ ] Moves to Done/

**Dependencies**: T2.5

---

### T2.7: Test Invoice Creator End-to-End
**Priority**: High
**Estimated Time**: 30 minutes
**Status**: Not Started

**Description**: Test complete invoice creation workflow

**Test Cases**:
1. Invoice for existing customer
2. Invoice for new customer
3. Invoice with multiple line items
4. Invoice rejection scenario

**Acceptance Criteria**:
- [ ] All test cases pass
- [ ] No errors in logs
- [ ] Approval workflow works
- [ ] Invoices created correctly in Odoo

**Dependencies**: T2.6

---

### T2.8: Create Payment Recorder Skill
**Priority**: High
**Estimated Time**: 3 hours
**Status**: Not Started

**Description**: Implement payment recording skill

**Steps**:
1. Create skill structure
2. Extract payment details from notifications
3. Search for matching invoices
4. Generate approval file
5. Record payment after approval
6. Update invoice status
7. Test end-to-end

**Acceptance Criteria**:
- [ ] Can extract payment details
- [ ] Matches payments to invoices
- [ ] Generates approval files
- [ ] Records payments in Odoo
- [ ] Updates invoice status

**Dependencies**: T2.7

---

### T2.9: Create Contact Manager Skill
**Priority**: High
**Estimated Time**: 3 hours
**Status**: Not Started

**Description**: Implement customer contact management skill

**Steps**:
1. Create skill structure
2. Extract contact details from emails/messages
3. Check for duplicates in Odoo
4. Generate approval file
5. Create contact after approval
6. Sync to vault
7. Test end-to-end

**Acceptance Criteria**:
- [ ] Can extract contact details
- [ ] Detects duplicates
- [ ] Generates approval files
- [ ] Creates contacts in Odoo
- [ ] Syncs to vault

**Dependencies**: T2.7

---

## Phase 3: Reporting & Integration (7 hours)

### T3.1: Create Expense Tracker Skill
**Priority**: Medium
**Estimated Time**: 3 hours
**Status**: Not Started

**Description**: Implement expense tracking and categorization

**Steps**:
1. Create skill structure
2. Extract expense details from receipts
3. Suggest expense category
4. Generate approval file
5. Create expense in Odoo
6. Attach receipt document
7. Test end-to-end

**Acceptance Criteria**:
- [ ] Can extract expense details
- [ ] Suggests correct categories
- [ ] Generates approval files
- [ ] Creates expenses in Odoo
- [ ] Attaches receipts

**Dependencies**: T2.9

---

### T3.2: Create Financial Report Generator Skill
**Priority**: Medium
**Estimated Time**: 4 hours
**Status**: Not Started

**Description**: Generate financial data for CEO briefings

**Steps**:
1. Create skill structure
2. Fetch revenue/expense data from Odoo
3. Calculate profit/loss and growth
4. Detect subscription patterns
5. Generate financial summary
6. Add to CEO briefing template
7. Test with real data

**Acceptance Criteria**:
- [ ] Fetches financial data from Odoo
- [ ] Calculates metrics correctly
- [ ] Detects subscriptions
- [ ] Generates readable summary
- [ ] Integrates with briefing

**Dependencies**: T3.1

---

### T3.3: Integrate with Weekly Audit Orchestrator
**Priority**: Medium
**Estimated Time**: 1 hour (included in T3.2)
**Status**: Not Started

**Description**: Add Odoo reporting to weekly audit

**Steps**:
1. Modify `app/src/app/weekly_audit/audit_orchestrator.py`
2. Add Odoo report generator call
3. Include financial section in briefing
4. Test weekly audit run

**Acceptance Criteria**:
- [ ] Audit orchestrator calls Odoo report generator
- [ ] Financial data included in briefing
- [ ] No errors during audit run

**Dependencies**: T3.2

---

## Phase 4: Approval Workflow Integration (3 hours)

### T4.1: Define Approval Thresholds
**Priority**: High
**Estimated Time**: 30 minutes
**Status**: Not Started

**Description**: Document approval rules in Company Handbook

**Steps**:
1. Open `AI_Employee_Vault/Company_Handbook.md`
2. Add "Accounting Approval Thresholds" section
3. Define thresholds for:
   - Invoices (all require approval initially)
   - Payments (>$100)
   - Expenses (>$50)
   - Customers (all require approval)
4. Save and commit

**Acceptance Criteria**:
- [ ] Thresholds documented in handbook
- [ ] Clear rules for each operation type
- [ ] Examples provided

**Dependencies**: None

---

### T4.2: Implement Approval Monitoring
**Priority**: High
**Estimated Time**: 1 hour
**Status**: Not Started

**Description**: Monitor approval directories and process approvals

**Steps**:
1. Create approval monitor script
2. Check `Pending_Approval/accounting/` every 5 minutes
3. Process files in `Approved/` directory
4. Log files in `Rejected/` directory
5. Send reminders after 24 hours
6. Escalate after 48 hours

**Acceptance Criteria**:
- [ ] Monitors approval directories
- [ ] Processes approved operations
- [ ] Logs rejected operations
- [ ] Sends reminders
- [ ] Escalates when needed

**Dependencies**: T4.1

---

### T4.3: Update Dashboard with Odoo Status
**Priority**: Medium
**Estimated Time**: 1 hour
**Status**: Not Started

**Description**: Add Odoo metrics to Dashboard.md

**Steps**:
1. Open `AI_Employee_Vault/Dashboard.md`
2. Add "Odoo Integration" section
3. Show:
   - Connection status
   - Pending approvals count
   - Recent invoices (last 7 days)
   - Recent payments (last 7 days)
   - Financial summary
4. Update dashboard update script

**Acceptance Criteria**:
- [ ] Dashboard shows Odoo status
- [ ] Metrics update automatically
- [ ] Readable format

**Dependencies**: T4.2

---

### T4.4: Implement Logging for Odoo Operations
**Priority**: High
**Estimated Time**: 30 minutes
**Status**: Not Started

**Description**: Log all Odoo operations for audit trail

**Steps**:
1. Create `Logs/Accounting/` directory
2. Create `odoo_operations.log` file
3. Log format: timestamp, operation, user/agent, result
4. Implement daily log rotation
5. Integrate with error recovery system

**Acceptance Criteria**:
- [ ] All operations logged
- [ ] Log format consistent
- [ ] Daily rotation works
- [ ] Logs readable and searchable

**Dependencies**: None

---

## Phase 5: Testing & Validation (3 hours)

### T5.1: Create Unit Tests for Skills
**Priority**: Medium
**Estimated Time**: 1 hour
**Status**: Not Started

**Description**: Write unit tests for each skill

**Steps**:
1. Create test file for each skill
2. Test data extraction functions
3. Test MCP tool calls (mocked)
4. Test error handling
5. Test approval file generation

**Acceptance Criteria**:
- [ ] Tests for invoice creator
- [ ] Tests for payment recorder
- [ ] Tests for contact manager
- [ ] Tests for expense tracker
- [ ] Tests for report generator
- [ ] All tests pass

**Dependencies**: T3.3

---

### T5.2: Run Integration Tests
**Priority**: High
**Estimated Time**: 1 hour
**Status**: Not Started

**Description**: Test end-to-end workflows with real Odoo

**Test Scenarios**:
1. Email arrives → Invoice created → Approved → Posted
2. Payment notification → Matched → Approved → Recorded
3. New contact → Detected → Approved → Created
4. Expense receipt → Categorized → Approved → Recorded
5. Weekly audit → Financial data → Briefing generated

**Acceptance Criteria**:
- [ ] All scenarios complete successfully
- [ ] No errors in logs
- [ ] Data correct in Odoo
- [ ] Approval workflow works

**Dependencies**: T5.1

---

### T5.3: Test Error Scenarios
**Priority**: High
**Estimated Time**: 1 hour
**Status**: Not Started

**Description**: Verify error handling and recovery

**Test Cases**:
1. Odoo unavailable (queue operations)
2. Invalid data (request clarification)
3. Duplicate records (detect and prevent)
4. Timeout (retry with backoff)
5. Authentication failure (alert user)

**Acceptance Criteria**:
- [ ] All error cases handled gracefully
- [ ] Operations queued when Odoo down
- [ ] Clear error messages
- [ ] No data loss

**Dependencies**: T5.2

---

## Phase 6: Documentation & Deployment (2 hours)

### T6.1: Update User Guide
**Priority**: Medium
**Estimated Time**: 45 minutes
**Status**: Not Started

**Description**: Document Odoo operations in user guide

**Steps**:
1. Open `USER_GUIDE.md`
2. Add "Odoo Integration" section
3. Document:
   - How to create invoices
   - How to record payments
   - How to manage contacts
   - How to track expenses
   - How to view financial reports
4. Add troubleshooting tips

**Acceptance Criteria**:
- [ ] User guide updated
- [ ] All operations documented
- [ ] Examples provided
- [ ] Troubleshooting section added

**Dependencies**: T5.3

---

### T6.2: Create Troubleshooting Guide
**Priority**: Medium
**Estimated Time**: 30 minutes
**Status**: Not Started

**Description**: Document common issues and solutions

**Steps**:
1. Create troubleshooting section in setup guide
2. Document common errors:
   - Connection failures
   - Authentication errors
   - Timeout issues
   - Data sync problems
3. Provide solutions for each

**Acceptance Criteria**:
- [ ] Common issues documented
- [ ] Solutions provided
- [ ] Easy to follow

**Dependencies**: T6.1

---

### T6.3: Final Testing and Validation
**Priority**: High
**Estimated Time**: 45 minutes
**Status**: Not Started

**Description**: Complete final validation before deployment

**Steps**:
1. Run all tests
2. Verify all skills work
3. Check approval workflow
4. Verify logging
5. Test with real business scenarios
6. Get user feedback

**Acceptance Criteria**:
- [ ] All tests pass
- [ ] All skills functional
- [ ] Approval workflow works
- [ ] Logging complete
- [ ] User satisfied

**Dependencies**: T6.2

---

## Task Dependencies Graph

```
T1.1 (Install Odoo)
  └─> T1.2 (Create Database)
       └─> T1.3 (Install Apps)
            └─> T1.4 (Generate API Key)
                 └─> T1.5 (Update .env)
                      └─> T1.7 (Test Connection)
                           └─> T1.8 (Add Test Data)
                                └─> T2.1 (Invoice Skill Structure)
                                     └─> T2.2 → T2.3 → T2.4 → T2.5 → T2.6 → T2.7
                                          └─> T2.8 (Payment Skill)
                                          └─> T2.9 (Contact Skill)
                                               └─> T3.1 (Expense Skill)
                                                    └─> T3.2 (Report Generator)
                                                         └─> T3.3 (Audit Integration)
                                                              └─> T5.1 → T5.2 → T5.3
                                                                   └─> T6.1 → T6.2 → T6.3

T1.6 (Test MCP Server) → T1.7

T4.1 (Approval Thresholds) → T4.2 (Approval Monitoring) → T4.3 (Dashboard)
T4.4 (Logging) - Independent
```

---

## Progress Tracking

**Phase 1**: 0/8 tasks complete (0%)
**Phase 2**: 0/9 tasks complete (0%)
**Phase 3**: 0/3 tasks complete (0%)
**Phase 4**: 0/4 tasks complete (0%)
**Phase 5**: 0/3 tasks complete (0%)
**Phase 6**: 0/3 tasks complete (0%)

**Overall**: 0/30 tasks complete (0%)

---

## Next Immediate Steps

1. **T1.1**: Install Odoo (choose local or cloud)
2. **T1.2**: Create database
3. **T1.3**: Install apps
4. **T1.4**: Generate API key
5. **T1.5**: Update .env file

**Start here**: Follow `guides/ODOO_SETUP_GUIDE.md` to complete T1.1-T1.5

---

**Tasks Version**: 1.0
**Last Updated**: 2026-02-27
**Status**: Ready to start