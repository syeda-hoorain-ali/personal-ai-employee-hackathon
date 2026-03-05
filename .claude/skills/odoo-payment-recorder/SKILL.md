# Odoo Payment Recorder

**Record payments and match them to invoices automatically**

---

## Purpose

Automatically record payments in Odoo when payment notifications arrive via email or WhatsApp. Matches payments to invoices and updates invoice status.

---

## When to Use

**Trigger phrases:**
- "Record payment from [customer]"
- "Payment received: $[amount]"
- "[Customer] paid invoice [number]"
- Bank notification emails with payment details

---

## What It Does

1. **Extracts payment details**: Amount, date, customer name, reference
2. **Searches for matching invoice**: By customer, amount, or invoice number
3. **Handles ambiguous matches**: Asks for clarification if multiple invoices match
4. **Creates approval file**: In `Pending_Approval/accounting/`
5. **Records payment**: After approval, creates payment record in Odoo
6. **Updates invoice**: Marks invoice as paid (full or partial)
7. **Logs operation**: Records in `Logs/Accounting/`

---

## Usage Example

**Request:**
```
Payment received from Acme Corp - $1,650 for invoice INV/2026/0042
```

**AI Response:**
```
I'll record the payment from Acme Corp.

Found invoice: INV/2026/0042
- Customer: Acme Corporation
- Amount: $1,650.00
- Status: Open

Payment matches invoice exactly.

Creating approval request...
Please review and approve to record payment in Odoo.
```

---

## Odoo MCP Tools Used

```javascript
// Search for invoice
search_records({
  model: "account.move",
  domain: [
    ["partner_id.name", "ilike", "Acme"],
    ["amount_total", "=", 1650.00],
    ["state", "=", "posted"]
  ]
})

// Create payment
create_record({
  model: "account.payment",
  values: {
    payment_type: "inbound",
    partner_id: 45,
    amount: 1650.00,
    date: "2026-02-27",
    ref: "Payment for INV/2026/0042"
  }
})

// Link payment to invoice
execute_method({
  model: "account.payment",
  method: "action_post",
  ids: [payment_id]
})
```

---

## Approval File Format

**Location:** `Pending_Approval/accounting/PAYMENT_<customer>_<amount>.md`

```markdown
---
type: payment
customer: Acme Corporation
amount: 1650.00
invoice_number: INV/2026/0042
date: 2026-02-27
---

# Payment Approval Request

**Customer**: Acme Corporation
**Amount**: $1,650.00
**Date**: February 27, 2026

## Matched Invoice

- **Invoice**: INV/2026/0042
- **Original Amount**: $1,650.00
- **Amount Paid**: $0.00
- **Remaining**: $1,650.00

## Payment Details

- **Payment Method**: Bank Transfer
- **Reference**: Payment for consulting services

## Actions

✅ **To approve**: Move to `Approved/accounting/`
❌ **To reject**: Move to `Rejected/accounting/`
```

---

## Error Handling

- **No matching invoice**: Ask for invoice number or customer clarification
- **Multiple matches**: List all matches and ask which one
- **Overpayment**: Create credit note for excess amount
- **Partial payment**: Record partial payment and update remaining balance

---

## Configuration

```env
ODOO_URL=https://your-odoo.odoo.com
ODOO_API_KEY=your_api_key
ODOO_DB=your_database
```

---

**Version**: 1.0 | **Created**: 2026-02-27