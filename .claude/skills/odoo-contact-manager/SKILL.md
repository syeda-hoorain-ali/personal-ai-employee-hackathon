# Odoo Contact Manager

**Manage customer and supplier contacts in Odoo automatically**

---

## Purpose

Automatically create and update customer/supplier contacts in Odoo when detected from emails, WhatsApp messages, or invoice requests.

---

## When to Use

**Trigger phrases:**
- "Add customer [name]"
- "Create contact for [company]"
- "Update [customer] email to [email]"
- New email signatures with contact details
- Invoice requests for unknown customers

---

## What It Does

1. **Extracts contact details**: Name, email, phone, company, address
2. **Checks for duplicates**: Searches Odoo for existing contacts
3. **Creates approval file**: In `Pending_Approval/accounting/`
4. **Creates/updates contact**: After approval, creates or updates in Odoo
5. **Syncs to vault**: Exports customer list to `References/customers.md`
6. **Logs operation**: Records in `Logs/Accounting/`

---

## Usage Example

**Request:**
```
Add new customer:
- Name: Jane Smith
- Company: Tech Solutions Inc
- Email: jane@techsolutions.com
- Phone: +1-555-0199
```

**AI Response:**
```
I'll create a new customer contact in Odoo.

Checking for duplicates...
No existing contact found for "Tech Solutions Inc"

Creating approval request for:
- Name: Jane Smith
- Company: Tech Solutions Inc
- Email: jane@techsolutions.com
- Phone: +1-555-0199
- Type: Company

Please review and approve to create in Odoo.
```

---

## Odoo MCP Tools Used

```javascript
// Check for duplicates
search_records({
  model: "res.partner",
  domain: [
    "|",
    ["name", "ilike", "Tech Solutions"],
    ["email", "=", "jane@techsolutions.com"]
  ]
})

// Create contact
create_record({
  model: "res.partner",
  values: {
    name: "Tech Solutions Inc",
    email: "jane@techsolutions.com",
    phone: "+1-555-0199",
    is_company: true,
    customer_rank: 1
  }
})

// Update existing contact
update_record({
  model: "res.partner",
  id: 45,
  values: {
    phone: "+1-555-0199",
    email: "newemail@example.com"
  }
})
```

---

## Approval File Format

**Location:** `Pending_Approval/accounting/CUSTOMER_<name>.md`

```markdown
---
type: customer
name: Tech Solutions Inc
email: jane@techsolutions.com
phone: +1-555-0199
---

# Customer Creation Request

**Company**: Tech Solutions Inc
**Contact Person**: Jane Smith
**Email**: jane@techsolutions.com
**Phone**: +1-555-0199
**Type**: Company

## Actions

✅ **To approve**: Move to `Approved/accounting/`
❌ **To reject**: Move to `Rejected/accounting/`
```

---

## Duplicate Detection

**Checks for duplicates by:**
- Exact email match
- Similar company name (fuzzy matching)
- Phone number match

**If duplicate found:**
```
Found existing contact: Tech Solutions Inc (ID: 45)
- Email: jane@techsolutions.com
- Phone: +1-555-0100

Would you like to:
1. Update existing contact
2. Create new contact anyway
3. Cancel operation
```

---

## Vault Sync

**Daily sync to:** `References/customers.md`

```markdown
# Customer List

Last updated: 2026-02-27

## Active Customers

1. **Acme Corporation**
   - Email: contact@acme.com
   - Phone: +1-555-0123
   - Odoo ID: 45

2. **Tech Solutions Inc**
   - Email: jane@techsolutions.com
   - Phone: +1-555-0199
   - Odoo ID: 78
```

---

## Configuration

```env
ODOO_URL=https://your-odoo.odoo.com
ODOO_API_KEY=your_api_key
ODOO_DB=your_database
```

---

**Version**: 1.0 | **Created**: 2026-02-27
