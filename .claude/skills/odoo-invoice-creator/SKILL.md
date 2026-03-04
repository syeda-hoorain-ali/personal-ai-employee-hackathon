# Odoo Invoice Creator

**Create draft invoices in Odoo from natural language requests with approval workflow**

---

## Purpose

Automatically create invoices in Odoo when clients request them via email or WhatsApp. The AI extracts invoice details, creates a draft invoice in Odoo, and requests approval before posting and sending.

---

## When to Use This Skill

**Trigger phrases:**
- "Create an invoice for [customer]"
- "Send invoice to [customer]"
- "Bill [customer] for [services]"
- "Generate invoice for [project/work]"
- Client requests: "Can you send me an invoice?"

**Use this skill when:**
- Client requests an invoice via email/WhatsApp
- You need to bill a customer for completed work
- Creating recurring invoices (monthly retainers, subscriptions)
- Converting quotes to invoices

---

## What This Skill Does

1. **Extracts invoice details** from the request:
   - Customer name
   - Line items (description, quantity, unit price)
   - Payment terms and due date
   - Any special notes or references

2. **Searches Odoo for the customer**:
   - Finds existing customer by name
   - If multiple matches, asks for clarification
   - If no match, triggers customer creation workflow

3. **Reads Company Handbook** for rates and terms:
   - Standard hourly rates
   - Product/service pricing
   - Default payment terms
   - Tax rates

4. **Creates draft invoice in Odoo**:
   - Uses Odoo MCP `create_record` tool
   - Sets customer, line items, terms
   - Keeps invoice in draft status

5. **Generates approval file**:
   - Creates markdown file in `Pending_Approval/accounting/`
   - Includes invoice preview with all details
   - Provides link to Odoo draft invoice

6. **After approval**:
   - Posts invoice in Odoo (changes status to "Posted")
   - Sends invoice via email to customer
   - Logs operation in `Logs/Accounting/`
   - Moves task to `Done/accounting/`

---

## How to Use

### Basic Usage

**User request:**
```
Create an invoice for Acme Corporation:
- Consulting services: 10 hours at $150/hour
- Due in 30 days
```

**AI response:**
```
I'll create an invoice for Acme Corporation.

Let me search for this customer in Odoo...
Found: Acme Corporation (ID: 45)

Creating draft invoice with:
- Line item: Consulting services - 10 hours × $150.00 = $1,500.00
- Subtotal: $1,500.00
- Tax (10%): $150.00
- Total: $1,650.00
- Payment terms: Net 30 days
- Due date: 2026-03-29

Draft invoice created in Odoo (INV/2026/0042)

I've created an approval request in Pending_Approval/accounting/
Please review the invoice in Odoo and approve to send to customer.
```

### With Missing Information

**User request:**
```
Create an invoice for John
```

**AI response:**
```
I'll create an invoice for John. I need some additional information:

1. Which John? I found multiple customers:
   - John Doe (john@example.com)
   - John Smith (john.smith@company.com)

2. What services/products should I include?

3. What's the amount or hourly rate?

Please provide these details so I can create the invoice.
```

### For New Customer

**User request:**
```
Create an invoice for New Client Corp for $2,500
```

**AI response:**
```
I couldn't find "New Client Corp" in Odoo.

Would you like me to:
1. Create a new customer record first (requires approval)
2. Use a different customer name
3. Provide more details about this customer

Please let me know how to proceed.
```

---

## Approval Workflow

### Approval File Format

**Location:** `Pending_Approval/accounting/INVOICE_<customer>_<date>.md`

**Example:**
```markdown
---
type: invoice
customer: Acme Corporation
customer_id: 45
amount: 1650.00
currency: USD
date: 2026-02-27
due_date: 2026-03-29
status: pending
odoo_invoice_id: 123
---

# Invoice Approval Request

**Customer**: Acme Corporation (acme@example.com)
**Invoice Number**: INV/2026/0042 (draft)
**Amount**: $1,650.00
**Due Date**: March 29, 2026

## Line Items

| Description | Quantity | Unit Price | Total |
|-------------|----------|------------|-------|
| Consulting Services | 10 hours | $150.00 | $1,500.00 |

**Subtotal**: $1,500.00
**Tax (10%)**: $150.00
**Total**: $1,650.00

## Payment Terms

Net 30 days

## Actions

✅ **To approve**: Move this file to `Approved/accounting/`
❌ **To reject**: Move this file to `Rejected/accounting/`

**Odoo Draft Invoice**: https://personal-ai-employee1.odoo.com/web#id=123&model=account.move

---

*Created by AI Employee on 2026-02-27 at 14:30*
```

### After Approval

When you move the file to `Approved/accounting/`:

1. AI detects the approval
2. Posts the invoice in Odoo (status: draft → posted)
3. Sends invoice via email to customer
4. Logs operation:
   ```
   2026-02-27 14:35 | INVOICE_POSTED | Acme Corporation | INV/2026/0042 | $1,650.00 | SUCCESS
   ```
5. Moves task to `Done/accounting/`

### After Rejection

When you move the file to `Rejected/accounting/`:

1. AI detects the rejection
2. Deletes draft invoice in Odoo (optional)
3. Logs rejection:
   ```
   2026-02-27 14:35 | INVOICE_REJECTED | Acme Corporation | INV/2026/0042 | $1,650.00 | User rejected
   ```
4. Notifies you of rejection

---

## Integration with Company Handbook

The skill reads `Company_Handbook.md` for:

### Standard Rates

```markdown
## Service Rates

- Consulting: $150/hour
- Development: $200/hour
- Design: $175/hour
- Support: $100/hour
```

### Payment Terms

```markdown
## Payment Terms

- Standard: Net 30 days
- Rush projects: Net 15 days
- Retainer clients: Net 45 days
```

### Tax Configuration

```markdown
## Tax Rates

- Standard rate: 10%
- Exempt customers: 0%
- International: 0% (reverse charge)
```

---

## Odoo MCP Tools Used

### 1. Search for Customer

```javascript
search_records({
  model: "res.partner",
  domain: [["name", "ilike", "Acme Corporation"]],
  fields: ["id", "name", "email", "phone"],
  limit: 10
})
```

### 2. Create Draft Invoice

```javascript
create_record({
  model: "account.move",
  values: {
    partner_id: 45,
    move_type: "out_invoice",
    invoice_date: "2026-02-27",
    invoice_date_due: "2026-03-29",
    invoice_line_ids: [
      {
        name: "Consulting Services",
        quantity: 10,
        price_unit: 150.00,
        account_id: 400  // Revenue account
      }
    ]
  }
})
```

### 3. Post Invoice (After Approval)

```javascript
update_record({
  model: "account.move",
  id: 123,
  values: {
    state: "posted"
  }
})
```

### 4. Send Invoice via Email

```javascript
execute_method({
  model: "account.move",
  method: "action_invoice_sent",
  ids: [123]
})
```

---

## Error Handling

### Customer Not Found

**Error:** No customer matches the name

**Solution:**
1. Ask for clarification (spelling, company name)
2. Offer to create new customer
3. Show similar customer names

### Multiple Customers Match

**Error:** Multiple customers with similar names

**Solution:**
1. List all matches with email/phone
2. Ask user to specify which one
3. Use customer ID if provided

### Missing Line Items

**Error:** No products/services specified

**Solution:**
1. Ask what to include in invoice
2. Suggest common services from handbook
3. Request quantity and price

### Odoo Connection Error

**Error:** Cannot connect to Odoo

**Solution:**
1. Queue the invoice creation
2. Retry automatically every 5 minutes
3. Alert user after 3 failed attempts
4. Log error for troubleshooting

### Invalid Data

**Error:** Invalid amount, date, or customer data

**Solution:**
1. Validate data before creating invoice
2. Request correction from user
3. Provide clear error message
4. Log validation error

---

## Examples

### Example 1: Simple Invoice

**Request:**
```
Create invoice for ABC Company - $1,000 for web development
```

**Process:**
1. Search Odoo for "ABC Company"
2. Found customer (ID: 78)
3. Create invoice with single line item
4. Generate approval file
5. Wait for approval

**Result:**
- Draft invoice INV/2026/0043 created
- Approval file in Pending_Approval/accounting/
- User reviews and approves
- Invoice posted and sent

### Example 2: Multiple Line Items

**Request:**
```
Invoice for XYZ Corp:
- Website design: 20 hours
- Logo design: 5 hours
- Hosting setup: 1 month
```

**Process:**
1. Search for XYZ Corp
2. Read rates from Company_Handbook.md:
   - Design: $175/hour
   - Hosting: $50/month
3. Calculate totals:
   - Website: 20 × $175 = $3,500
   - Logo: 5 × $175 = $875
   - Hosting: 1 × $50 = $50
   - Total: $4,425
4. Create invoice with 3 line items
5. Generate approval file

**Result:**
- Invoice with itemized services
- Clear breakdown of charges
- Professional presentation

### Example 3: Recurring Invoice

**Request:**
```
Create monthly retainer invoice for Client A - $5,000
```

**Process:**
1. Search for Client A
2. Check if recurring invoice exists
3. Create new invoice for current month
4. Reference previous invoices
5. Apply retainer payment terms (Net 45)

**Result:**
- Consistent monthly billing
- Automatic payment terms
- Historical reference

---

## Best Practices

### 1. Always Verify Customer

- Double-check customer name spelling
- Confirm email address is correct
- Verify billing address if needed

### 2. Use Standard Rates

- Reference Company_Handbook.md for rates
- Apply consistent pricing
- Document any discounts or special rates

### 3. Clear Line Item Descriptions

- Be specific about services provided
- Include dates or project names
- Add reference numbers if applicable

### 4. Review Before Approval

- Check all amounts are correct
- Verify tax calculations
- Confirm payment terms
- Review customer details

### 5. Track Invoice Status

- Monitor approval queue
- Follow up on pending approvals
- Track sent invoices in Odoo

---

## Troubleshooting

### Issue: "Customer not found in Odoo"

**Check:**
1. Customer name spelling
2. Customer exists in Odoo Contacts
3. Customer is not archived

**Fix:**
- Create customer first using `odoo-contact-manager` skill
- Or provide customer ID directly

### Issue: "Invoice creation failed"

**Check:**
1. Odoo connection status
2. Required fields provided
3. Valid account codes
4. Tax configuration

**Fix:**
- Verify .env has correct ODOO_URL and ODOO_API_KEY
- Check Odoo logs for errors
- Ensure all required fields present

### Issue: "Approval file not detected"

**Check:**
1. File in correct directory
2. File name format correct
3. Approval monitoring running

**Fix:**
- Verify file in `Pending_Approval/accounting/`
- Check file name: `INVOICE_<customer>_<date>.md`
- Restart approval monitoring

---

## Configuration

### Required Environment Variables

```env
ODOO_URL=https://your-odoo-instance.odoo.com
ODOO_DB=your_database_name
ODOO_API_KEY=your_api_key_here
ODOO_YOLO=read  # or 'true' for write access
```

### Required Odoo Apps

- Accounting
- Invoicing
- Contacts

### Required Vault Directories

- `Pending_Approval/accounting/`
- `Approved/accounting/`
- `Rejected/accounting/`
- `Done/accounting/`
- `Logs/Accounting/`

---

## Related Skills

- **odoo-contact-manager**: Create/update customers before invoicing
- **odoo-payment-recorder**: Record payments for invoices
- **odoo-report-generator**: Generate financial reports including invoices
- **needs-action-processor**: Process invoice requests from Needs_Action/

---

## Skill Metadata

- **Version**: 1.0
- **Created**: 2026-02-27
- **Dependencies**: Odoo MCP server, Company_Handbook.md
- **Approval Required**: Yes (all invoices)
- **Estimated Time**: 2-5 minutes per invoice

---

## Success Metrics

Track these metrics to measure skill effectiveness:

- **Automation Rate**: % of invoices created automatically
- **Approval Time**: Average time from creation to approval
- **Error Rate**: % of invoices that fail to create
- **Customer Satisfaction**: Feedback on invoice accuracy
- **Time Savings**: Hours saved vs manual invoice creation

**Target Metrics:**
- 90% automation rate
- < 2 hours approval time
- < 1% error rate
- 10+ hours saved per week