# Odoo Expense Tracker

**Track and categorize business expenses automatically**

---

## Purpose

Automatically record expenses in Odoo when receipts arrive via email or when expenses are reported via WhatsApp. Categorizes expenses according to chart of accounts.

---

## When to Use

**Trigger phrases:**
- "Record expense: [description] - $[amount]"
- "Add expense for [vendor]"
- Email with receipt attachment
- "Track expense: [details]"

---

## What It Does

1. **Extracts expense details**: Vendor, amount, date, category, description
2. **Suggests category**: Based on vendor name and expense type
3. **Creates approval file**: In `Pending_Approval/accounting/`
4. **Records expense**: After approval, creates expense record in Odoo
5. **Attaches receipt**: Links receipt document if available
6. **Logs operation**: Records in `Logs/Accounting/`

---

## Usage Example

**Request:**
```
Record expense:
- Vendor: Adobe
- Amount: $52.99
- Description: Creative Cloud subscription
- Date: 2026-02-27
```

**AI Response:**
```
I'll record this expense in Odoo.

Expense details:
- Vendor: Adobe
- Amount: $52.99
- Category: Software Subscriptions (suggested)
- Date: February 27, 2026

Creating approval request...
Please review and approve to record in Odoo.
```

---

## Odoo MCP Tools Used

```javascript
// Search for expense accounts
search_records({
  model: "account.account",
  domain: [
    ["account_type", "=", "expense"],
    ["name", "ilike", "software"]
  ]
})

// Create expense
create_record({
  model: "account.move",
  values: {
    move_type: "in_invoice",
    partner_id: vendor_id,
    invoice_date: "2026-02-27",
    invoice_line_ids: [{
      name: "Creative Cloud subscription",
      quantity: 1,
      price_unit: 52.99,
      account_id: expense_account_id
    }]
  }
})
```

---

## Expense Categories

**Auto-categorization based on vendor:**
- Adobe, Microsoft → Software Subscriptions
- AWS, DigitalOcean → Cloud Services
- Starbucks, restaurants → Meals & Entertainment
- Uber, Lyft → Travel & Transportation
- Office Depot → Office Supplies

---

## Approval File Format

**Location:** `Pending_Approval/accounting/EXPENSE_<vendor>_<amount>.md`

```markdown
---
type: expense
vendor: Adobe
amount: 52.99
category: Software Subscriptions
date: 2026-02-27
---

# Expense Approval Request

**Vendor**: Adobe
**Amount**: $52.99
**Category**: Software Subscriptions
**Date**: February 27, 2026

## Description

Creative Cloud subscription - monthly

## Actions

✅ **To approve**: Move to `Approved/accounting/`
❌ **To reject**: Move to `Rejected/accounting/`
```

---

## Subscription Detection

**Automatically detects recurring expenses:**
- Monthly subscriptions (Adobe, Microsoft, etc.)
- Annual renewals (domain names, SSL certificates)
- Quarterly payments (insurance, taxes)

**Alerts for unusual patterns:**
- Subscription price increase
- New subscription detected
- Duplicate subscription

---

## Configuration

```env
ODOO_URL=https://your-odoo.odoo.com
ODOO_API_KEY=your_api_key
ODOO_DB=your_database
```

---

**Version**: 1.0 | **Created**: 2026-02-27
