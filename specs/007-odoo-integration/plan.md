# Odoo Integration Implementation Plan

**Feature**: 007-odoo-integration
**Status**: Planning
**Created**: 2026-02-27

---

## Overview

Integrate Odoo Community Edition with Personal AI Employee to automate accounting, invoicing, customer management, and financial reporting.

**Goal**: Enable AI to handle 90% of routine accounting tasks autonomously with human approval for sensitive operations.

---

## Prerequisites

- [ ] Odoo installed (local or cloud) - See `guides/ODOO_SETUP_GUIDE.md`
- [ ] Odoo database created with Accounting, Contacts, Invoicing apps
- [ ] API key generated in Odoo
- [ ] `.env` file updated with Odoo credentials
- [ ] `.mcp.json` configured with Odoo MCP server
- [ ] UV package manager installed

---

## Phase 1: Setup & Testing (2 hours)

### 1.1 Verify MCP Connection

**Test MCP server can connect to Odoo:**

```bash
# Test MCP server installation
uvx mcp-server-odoo --help

# Test connection (set env vars first)
$env:ODOO_URL = "http://localhost:8069"  # or your cloud URL
$env:ODOO_DB = "my_business"
$env:ODOO_API_KEY = "your_api_key"
$env:ODOO_YOLO = "read"

# Run MCP server (Ctrl+C to stop)
uvx mcp-server-odoo
```

**Expected**: Server starts without errors

### 1.2 Test Basic Operations

**Restart Claude Code and test:**

```
1. "List all customers in Odoo"
2. "Show me the Odoo models available"
3. "Count how many contacts we have"
```

**Expected**: Claude uses Odoo MCP tools and returns data

### 1.3 Add Test Data

**In Odoo web interface, create:**
- 2 test customers
- 1 test product/service
- 1 test invoice (draft)

**Verify in Claude Code:**
```
"Show me all draft invoices in Odoo"
```

---

## Phase 2: Core Skills (10 hours)

### 2.1 Invoice Creator Skill (4 hours)

**Skill**: `odoo-invoice-creator`

**Purpose**: Create draft invoices in Odoo from natural language requests

**Workflow**:
1. Detect invoice request from email/WhatsApp
2. Extract: customer name, line items, amounts
3. Search Odoo for customer (create if not exists)
4. Read Company_Handbook.md for rates/terms
5. Create draft invoice in Odoo
6. Write approval file to `Pending_Approval/accounting/`
7. Wait for approval
8. Post invoice and send via email
9. Log operation and move to `Done/accounting/`

**MCP Tools Used**:
- `search_records` (find customer)
- `create_record` (create invoice)
- `update_record` (post invoice after approval)

**Test Cases**:
- Invoice for existing customer
- Invoice for new customer (requires customer creation)
- Invoice with multiple line items
- Invoice rejection scenario

### 2.2 Payment Recorder Skill (3 hours)

**Skill**: `odoo-payment-recorder`

**Purpose**: Record payments and match to invoices

**Workflow**:
1. Detect payment notification (email/WhatsApp)
2. Extract: amount, date, customer name, reference
3. Search Odoo for matching invoice
4. If ambiguous, request clarification
5. Write approval file to `Pending_Approval/accounting/`
6. After approval, record payment in Odoo
7. Update invoice status
8. Log operation and move to `Done/accounting/`

**MCP Tools Used**:
- `search_records` (find invoice)
- `create_record` (create payment)
- `update_record` (update invoice status)

**Test Cases**:
- Payment matches single invoice exactly
- Payment for multiple invoices (partial)
- Payment with no matching invoice
- Overpayment scenario

### 2.3 Contact Manager Skill (3 hours)

**Skill**: `odoo-contact-manager`

**Purpose**: Manage customer/supplier contacts in Odoo

**Workflow**:
1. Detect new contact from email signature/WhatsApp
2. Extract: name, email, phone, company, address
3. Check for duplicates in Odoo
4. Write approval file to `Pending_Approval/accounting/`
5. After approval, create contact in Odoo
6. Sync contact list to `References/customers.md`
7. Log operation

**MCP Tools Used**:
- `search_records` (check duplicates)
- `create_record` (create contact)
- `update_record` (update existing contact)

**Test Cases**:
- New customer from email
- Duplicate detection
- Update existing customer info
- Company vs individual contact

---

## Phase 3: Reporting & Integration (7 hours)

### 3.1 Expense Tracker Skill (3 hours)

**Skill**: `odoo-expense-tracker`

**Purpose**: Track and categorize expenses

**Workflow**:
1. Detect expense receipt (email attachment)
2. Extract: vendor, amount, date, category
3. Suggest expense category from chart of accounts
4. Write approval file to `Pending_Approval/accounting/`
5. After approval, create expense in Odoo
6. Attach receipt document
7. Log operation

**MCP Tools Used**:
- `search_records` (find expense accounts)
- `create_record` (create expense)

### 3.2 Financial Report Generator (4 hours) ✅ COMPLETED

**Skill**: `odoo-report-generator` ✅ Created

**Purpose**: Generate financial data for CEO briefings

**Workflow**:
1. Triggered weekly by trigger script (not orchestrator - architecture changed)
2. Fetch from Odoo:
   - Revenue (current week/month/year)
   - Expenses (current week/month/year)
   - Outstanding invoices
   - Overdue invoices
   - Cash flow projection
3. Calculate:
   - Net profit/loss
   - Week-over-week growth
   - Top customers by revenue
   - Top expense categories
4. Detect subscription patterns (recurring expenses)
5. Generate financial section for CEO briefing
6. Add to `Briefings/YYYY-MM-DD_DayName_Briefing.md`

**MCP Tools Used**:
- `search_records` (fetch financial data)
- Aggregation and analysis

**Integration Point**:
- ✅ Trigger script: `app/scripts/weekly_briefing_trigger.py`
- ✅ Skill: `.claude/skills/weekly-ceo-briefing/SKILL.md`
- ✅ Architecture: Trigger → Claude Code → Skills + MCP → Briefing

**Implementation Notes**:
- Changed from Python orchestrator to trigger-based system
- Claude Code acts as orchestrator (like LinkedIn poster)
- Skills provide knowledge, MCP tools provide actions
- More flexible and maintainable architecture

---

## Phase 4: Approval Workflow Integration (3 hours)

### 4.1 Approval File Format

**Standard format for accounting approvals:**

```markdown
---
type: invoice|payment|expense|customer
amount: $1,500.00
customer: Acme Corporation
date: 2026-02-27
status: pending
---

# Invoice Approval Request

**Customer**: Acme Corporation
**Amount**: $1,500.00
**Due Date**: 2026-03-15

## Line Items

| Description | Quantity | Unit Price | Total |
|-------------|----------|------------|-------|
| Consulting Services | 10 hours | $150.00 | $1,500.00 |

**Subtotal**: $1,500.00
**Tax (10%)**: $150.00
**Total**: $1,650.00

## Actions

- Move to `Approved/` to post invoice and send to customer
- Move to `Rejected/` to cancel

**Odoo Draft Invoice**: http://localhost:8069/web#id=123&model=account.move
```

### 4.2 Approval Thresholds

**Define in Company_Handbook.md:**

```markdown
## Accounting Approval Thresholds

- **Invoices**: All invoices require approval (initially)
- **Payments**: Payments over $100 require approval
- **Expenses**: Expenses over $50 require approval
- **Customers**: New customer creation requires approval
- **Expense Categories**: All categorization requires approval (initially)
```

### 4.3 Approval Monitoring

**Integrate with existing approval workflow:**
- Monitor `Pending_Approval/accounting/` every 5 minutes
- Process approved files (execute Odoo operations)
- Log rejected files with reason
- Send reminder after 24 hours
- Escalate after 48 hours

---

## Phase 5: Testing & Validation (3 hours)

### 5.1 Unit Tests

**Create tests for each skill:**
- Test MCP tool calls
- Test data extraction
- Test error handling
- Test approval file generation

### 5.2 Integration Tests

**End-to-end workflows:**
1. Email arrives → Invoice created → Approved → Posted → Sent
2. Payment notification → Matched → Approved → Recorded
3. New contact → Detected → Approved → Created
4. Expense receipt → Categorized → Approved → Recorded
5. Weekly audit → Financial data fetched → Briefing generated

### 5.3 Error Scenarios

**Test failure handling:**
- Odoo unavailable (queue operations)
- Invalid data (request clarification)
- Duplicate records (detect and prevent)
- Timeout (retry with backoff)
- Authentication failure (alert user)

---

## Phase 6: Documentation & Deployment (2 hours)

### 6.1 Update Documentation

- [ ] Update `USER_GUIDE.md` with Odoo operations
- [ ] Create troubleshooting section
- [ ] Document approval workflow
- [ ] Add example scenarios

### 6.2 Dashboard Integration

**Update `Dashboard.md` to show:**
- Odoo connection status
- Pending approvals count
- Recent invoices created
- Recent payments recorded
- Financial summary (weekly)

### 6.3 Logging & Monitoring

**Implement logging:**
- All Odoo operations logged to `Logs/Accounting/odoo_operations.log`
- Daily log rotation
- Error tracking in error recovery system
- Performance metrics (operation duration)

---

## Implementation Checklist

### Setup
- [ ] Install Odoo (local or cloud)
- [ ] Configure MCP server in `.mcp.json`
- [ ] Update `.env` with credentials
- [ ] Test MCP connection
- [ ] Add test data in Odoo

### Skills
- [ ] Create `odoo-invoice-creator` skill
- [ ] Create `odoo-payment-recorder` skill
- [ ] Create `odoo-contact-manager` skill
- [ ] Create `odoo-expense-tracker` skill
- [ ] Create `odoo-report-generator` skill

### Integration
- [ ] Integrate with approval workflow
- [ ] Add to weekly audit orchestrator
- [ ] Update Dashboard.md
- [ ] Configure logging

### Testing
- [ ] Test each skill individually
- [ ] Test end-to-end workflows
- [ ] Test error scenarios
- [ ] Verify approval workflow

### Documentation
- [ ] Update USER_GUIDE.md
- [ ] Create troubleshooting guide
- [ ] Document approval thresholds
- [ ] Add example scenarios

---

## Success Metrics

**After implementation, track:**
- **Automation Rate**: % of invoices created automatically
- **Approval Time**: Average time from request to approval
- **Error Rate**: % of operations that fail
- **Time Savings**: Hours saved per week
- **Data Quality**: Accuracy of financial records

**Target Metrics:**
- 90% automation rate for invoices
- < 2 hours average approval time
- < 1% error rate
- 10+ hours saved per week
- 99% data accuracy

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Odoo downtime | High | Queue operations, retry automatically |
| Incorrect amounts | High | Require approval for all operations initially |
| Payment matching errors | Medium | Manual review for ambiguous payments |
| Data sync conflicts | Medium | Odoo is source of truth |
| Security breach | Critical | Store credentials in .env, rotate keys monthly |

---

## Timeline

**Total Estimate**: 27 hours (~4 days)

- **Phase 1**: Setup & Testing - 2 hours
- **Phase 2**: Core Skills - 10 hours
- **Phase 3**: Reporting & Integration - 7 hours
- **Phase 4**: Approval Workflow - 3 hours
- **Phase 5**: Testing & Validation - 3 hours
- **Phase 6**: Documentation - 2 hours

**Recommended Schedule:**
- **Day 1**: Setup, testing, invoice creator skill
- **Day 2**: Payment recorder, contact manager skills
- **Day 3**: Expense tracker, report generator, approval integration
- **Day 4**: Testing, documentation, deployment

---

## Next Steps

1. **Install Odoo** (choose local or cloud from setup guide)
2. **Test MCP connection** (verify everything works)
3. **Create first skill** (start with invoice creator)
4. **Test with real data** (use actual business scenarios)
5. **Iterate and improve** (refine based on usage)

---

## References

- Setup Guide: `guides/ODOO_SETUP_GUIDE.md`
- MCP Server: https://github.com/ivnvxd/mcp-server-odoo
- Odoo API Docs: https://www.odoo.com/documentation/19.0/developer/reference/external_api.html
- Company Handbook: `AI_Employee_Vault/Company_Handbook.md`
- Approval Workflow: Silver Tier implementation

---

**Plan Version**: 1.0
**Last Updated**: 2026-02-27
**Status**: Ready for implementation