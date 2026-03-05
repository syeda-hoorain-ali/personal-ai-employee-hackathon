# Odoo Report Generator

**Generate financial reports and metrics for CEO briefings**

---

## Purpose

Automatically fetch financial data from Odoo and generate comprehensive reports for weekly CEO briefings. Provides insights into revenue, expenses, profit, outstanding invoices, and subscription patterns.

---

## When to Use

**Trigger phrases:**
- "Generate financial report"
- "Show me this week's revenue"
- "What's our profit this month?"
- Automatically triggered by weekly audit orchestrator

---

## What It Does

1. **Fetches financial data from Odoo**:
   - Revenue (week/month/year)
   - Expenses (week/month/year)
   - Outstanding invoices
   - Overdue invoices
   - Recent payments

2. **Calculates metrics**:
   - Net profit/loss
   - Week-over-week growth
   - Month-over-month growth
   - Cash flow projection

3. **Detects patterns**:
   - Recurring subscriptions
   - Unusual expenses
   - Late payments
   - Revenue trends

4. **Generates summary**:
   - Financial section for CEO briefing
   - Actionable insights
   - Alerts and warnings

5. **Adds to briefing**:
   - Inserts into `Briefings/YYYY-MM-DD_DayName_Briefing.md`
   - Formatted markdown tables
   - Visual indicators (✅ ⚠️ ❌)

---

## Usage Example

**Request:**
```
Generate financial report for this week
```

**AI Response:**
```
Fetching financial data from Odoo...

📊 Financial Summary (Feb 20-27, 2026)

Revenue: $12,450.00 (+15% vs last week)
Expenses: $3,200.00 (-5% vs last week)
Net Profit: $9,250.00

Outstanding Invoices: 3 ($8,500.00)
Overdue Invoices: 1 ($1,650.00) ⚠️

Top Customers:
1. Acme Corp - $5,000.00
2. Tech Solutions - $3,500.00
3. XYZ Inc - $2,450.00

Subscriptions Detected:
- Adobe Creative Cloud: $52.99/month
- AWS: $245.00/month
- Microsoft 365: $30.00/month

⚠️ Action Required:
- Follow up on overdue invoice from Client A ($1,650.00)
- 3 invoices pending approval

Report added to Monday briefing.
```

---

## Odoo MCP Tools Used

```javascript
// Fetch revenue (posted invoices)
search_records({
  model: "account.move",
  domain: [
    ["move_type", "=", "out_invoice"],
    ["state", "=", "posted"],
    ["invoice_date", ">=", "2026-02-20"],
    ["invoice_date", "<=", "2026-02-27"]
  ],
  fields: ["partner_id", "amount_total", "invoice_date"]
})

// Fetch expenses
search_records({
  model: "account.move",
  domain: [
    ["move_type", "=", "in_invoice"],
    ["state", "=", "posted"],
    ["invoice_date", ">=", "2026-02-20"]
  ],
  fields: ["partner_id", "amount_total", "invoice_date"]
})

// Fetch outstanding invoices
search_records({
  model: "account.move",
  domain: [
    ["move_type", "=", "out_invoice"],
    ["state", "=", "posted"],
    ["payment_state", "!=", "paid"]
  ],
  fields: ["partner_id", "amount_residual", "invoice_date_due"]
})

// Fetch payments
search_records({
  model: "account.payment",
  domain: [
    ["payment_type", "=", "inbound"],
    ["date", ">=", "2026-02-20"]
  ],
  fields: ["partner_id", "amount", "date"]
})
```

---

## Report Format

**Added to CEO Briefing:**

```markdown
## 💰 Financial Summary

**Period**: February 20-27, 2026

### Revenue & Expenses

| Metric | This Week | Last Week | Change |
|--------|-----------|-----------|--------|
| Revenue | $12,450.00 | $10,800.00 | +15% ✅ |
| Expenses | $3,200.00 | $3,370.00 | -5% ✅ |
| Net Profit | $9,250.00 | $7,430.00 | +24% ✅ |

### Outstanding Invoices

**Total Outstanding**: $8,500.00 (3 invoices)

| Customer | Invoice | Amount | Due Date | Status |
|----------|---------|--------|----------|--------|
| Client A | INV/2026/0040 | $1,650.00 | Feb 15 | ⚠️ Overdue |
| Acme Corp | INV/2026/0042 | $3,500.00 | Mar 15 | ✅ Current |
| Tech Solutions | INV/2026/0045 | $3,350.00 | Mar 20 | ✅ Current |

### Top Customers (This Week)

1. **Acme Corporation** - $5,000.00
2. **Tech Solutions Inc** - $3,500.00
3. **XYZ Company** - $2,450.00

### Recurring Expenses

| Subscription | Amount | Frequency | Next Due |
|--------------|--------|-----------|----------|
| Adobe Creative Cloud | $52.99 | Monthly | Mar 1 |
| AWS Cloud Services | $245.00 | Monthly | Mar 5 |
| Microsoft 365 | $30.00 | Monthly | Mar 10 |

**Total Monthly Subscriptions**: $327.99

### 🎯 Action Items

- ⚠️ **Follow up**: Client A invoice overdue by 12 days ($1,650.00)
- 📋 **Review**: 3 invoices pending approval in system
- 💡 **Insight**: Revenue up 15% - consulting services driving growth

---
```

---

## Subscription Detection

**Automatically identifies recurring expenses:**

1. **Pattern matching**: Same vendor, similar amount, regular intervals
2. **Frequency detection**: Monthly, quarterly, annual
3. **Trend analysis**: Price changes, new subscriptions
4. **Alerts**:
   - New subscription detected
   - Subscription price increased
   - Duplicate subscriptions found

**Example Alert:**
```
⚠️ Subscription Alert: Adobe Creative Cloud increased from $49.99 to $52.99 (+6%)
```

---

## Integration with Weekly Audit

**Automatically triggered by:** `app/src/app/weekly_audit/audit_orchestrator.py`

**Workflow:**
1. Weekly audit runs every Monday at 8 AM
2. Calls Odoo report generator
3. Fetches financial data from Odoo
4. Generates financial summary
5. Inserts into CEO briefing template
6. Saves to `Briefings/` directory

**Configuration in audit orchestrator:**
```python
# Add to audit_orchestrator.py
from odoo_report_generator import generate_financial_report

def run_weekly_audit():
    # ... existing code ...

    # Generate Odoo financial report
    financial_data = generate_financial_report(
        start_date=week_start,
        end_date=week_end
    )

    # Add to briefing
    briefing_content += financial_data

    # ... rest of briefing generation ...
```

---

## Metrics Tracked

### Revenue Metrics
- Total revenue (week/month/year)
- Revenue by customer
- Revenue by service/product
- Week-over-week growth
- Month-over-month growth

### Expense Metrics
- Total expenses (week/month/year)
- Expenses by category
- Expenses by vendor
- Subscription costs
- One-time vs recurring expenses

### Cash Flow Metrics
- Outstanding invoices (total)
- Overdue invoices (total)
- Average payment time
- Cash flow projection (30/60/90 days)

### Customer Metrics
- Top customers by revenue
- New customers this period
- Customer payment behavior
- Customer lifetime value

---

## Alerts & Warnings

**Automatic alerts for:**

✅ **Positive Indicators:**
- Revenue growth > 10%
- Expenses decreased
- All invoices paid on time
- New customer acquired

⚠️ **Warning Indicators:**
- Overdue invoices
- Revenue decline > 5%
- Expenses increased > 10%
- Late payments from customers

❌ **Critical Indicators:**
- Multiple overdue invoices
- Revenue decline > 20%
- Cash flow negative
- Subscription payment failed

---

## Configuration

```env
ODOO_URL=https://your-odoo.odoo.com
ODOO_API_KEY=your_api_key
ODOO_DB=your_database
```

**Briefing Configuration:**
```python
# In weekly_audit config
FINANCIAL_REPORT_ENABLED = True
REPORT_PERIOD = "week"  # week, month, quarter, year
INCLUDE_SUBSCRIPTIONS = True
INCLUDE_CUSTOMER_BREAKDOWN = True
ALERT_THRESHOLD_OVERDUE_DAYS = 7
```

---

## Error Handling

**If Odoo unavailable:**
```
⚠️ Financial data unavailable - Odoo connection failed
Using cached data from last successful sync (Feb 26, 2026)

Revenue (cached): $12,450.00
Expenses (cached): $3,200.00

Note: Data may be outdated. Retry connection in 5 minutes.
```

**If no data for period:**
```
ℹ️ No financial transactions for this period

Revenue: $0.00
Expenses: $0.00

This is unusual - please verify:
1. Odoo connection is working
2. Invoices are being created
3. Date range is correct
```

---

## Best Practices

### 1. Review Weekly
- Check financial summary every Monday
- Verify metrics are accurate
- Follow up on action items

### 2. Monitor Trends
- Track week-over-week growth
- Identify seasonal patterns
- Adjust business strategy accordingly

### 3. Act on Alerts
- Follow up on overdue invoices immediately
- Review unusual expenses
- Investigate revenue drops

### 4. Validate Data
- Cross-check with Odoo web interface
- Verify subscription amounts
- Confirm customer payments

---

## Troubleshooting

### Issue: "No financial data returned"

**Check:**
1. Odoo connection working
2. Date range correct
3. Invoices exist in Odoo
4. Invoices are posted (not draft)

**Fix:**
- Verify ODOO_URL and ODOO_API_KEY in .env
- Check date format (YYYY-MM-DD)
- Post draft invoices in Odoo

### Issue: "Subscription detection not working"

**Check:**
1. Multiple transactions from same vendor
2. Transactions span multiple months
3. Amounts are similar

**Fix:**
- Need at least 2 transactions to detect pattern
- Ensure vendor names are consistent
- Manual review if amounts vary significantly

---

## Related Skills

- **odoo-invoice-creator**: Creates invoices that appear in revenue
- **odoo-payment-recorder**: Records payments that update invoice status
- **odoo-expense-tracker**: Tracks expenses included in reports
- **update-dashboard**: Updates dashboard with financial metrics

---

## Skill Metadata

- **Version**: 1.0
- **Created**: 2026-02-27
- **Dependencies**: Odoo MCP server, weekly audit orchestrator
- **Approval Required**: No (read-only operation)
- **Estimated Time**: 30-60 seconds per report

---

## Success Metrics

**Track these metrics:**
- Report generation time
- Data accuracy (vs manual check)
- Actionable insights provided
- User satisfaction with insights

**Target Metrics:**
- < 60 seconds generation time
- 99% data accuracy
- 3+ actionable insights per report
- Weekly review completion rate > 90%

---

**Version**: 1.0 | **Created**: 2026-02-27
