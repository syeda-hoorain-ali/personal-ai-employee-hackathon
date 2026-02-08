# Email Processing Reference Guide

This guide outlines the various actions that can be taken when processing emails in the AI Employee system.

## Email Actions Overview

### 1. Reply to Sender
- **Trigger**: Email requires a response
- **Conditions**:
  - Questions needing answers
  - Requests for information
  - Follow-up required
- **Process**:
  - Analyze email content
  - Generate appropriate response
  - Send reply via email service
  - Update email status to "replied"

### 2. Forward to Relevant Party
- **Trigger**: Email needs forwarding to specific person/team
- **Conditions**:
  - Specialized knowledge required
  - Outside AI employee scope
  - Designated recipient exists
- **Process**:
  - Identify appropriate recipient
  - Prepare forwarding message
  - Include original email content
  - Send forwarded email

### 3. Request Approval
- **Trigger**: Email requires human oversight
- **Conditions**:
  - Financial transactions over threshold
  - Legal implications
  - Sensitive information requests
  - Unusual or suspicious requests
- **Process**:
  - Move to Pending_Approval folder
  - Create approval request
  - Notify human supervisor
  - Wait for approval/rejection

### 4. Draft Response
- **Trigger**: Complex email requiring human review
- **Conditions**:
  - Legal language needed
  - High-stakes communication
  - Brand-sensitive content
- **Process**:
  - Create draft response
  - Place in Drafts folder
  - Notify for human review
  - Await approval for sending

### 5. Move to Trash
- **Trigger**: Spam, phishing, or unwanted emails
- **Conditions**:
  - Identified spam content
  - Phishing attempts
  - Malicious links
  - Confirmed unwanted marketing
- **Process**:
  - Verify as unwanted
  - Move to Trash folder
  - Optionally delete permanently
  - Log deletion reason

### 6. Organize/Filing
- **Trigger**: Email needs categorization
- **Conditions**:
  - Specific project-related emails
  - Customer correspondence
  - Invoice/receipt emails
  - Meeting invitations
- **Process**:
  - Identify appropriate category
  - Move to relevant folder
  - Update metadata/tags
  - Index for search

### 7. Mark as Unread
- **Trigger**: Email needs revisit or follow-up
- **Conditions**:
  - Incomplete action items
  - Awaiting external input
  - Pending decision
- **Process**:
  - Preserve email status as unread
  - Add follow-up reminder
  - Track in pending items list

### 8. Mark/Unmark as Important
- **Trigger**: Priority assessment
- **Conditions**:
  - Urgent keywords detected
  - From VIP contacts
  - Financial/time-sensitive matters
  - Misclassified importance
- **Process**:
  - Assess importance criteria
  - Apply/remove important flag
  - Adjust processing priority
  - Update dashboard accordingly

### 9. Archive After Processing
- **Trigger**: Email fully processed
- **Conditions**:
  - All required actions completed
  - No further follow-up needed
  - Information extracted and stored
- **Process**:
  - Move to Archive folder
  - Update status to "completed"
  - Remove from active queue
  - Maintain searchable record

### 10. Schedule Response
- **Trigger**: Time-delayed responses needed
- **Conditions**:
  - Out-of-hours receipt
  - Strategic timing required
  - Batch processing scheduled
- **Process**:
  - Set future response time
  - Prepare response content
  - Queue for timed delivery
  - Monitor scheduling system

## Decision Tree for Email Actions

```
Email Received
├── Is it spam/phishing?
│   ├── YES → Move to Trash
│   └── NO → Continue
├── Does it require immediate financial commitment?
│   ├── YES → Request Approval
│   └── NO → Continue
├── Does it require specialized knowledge?
│   ├── YES → Forward to Relevant Party
│   └── NO → Continue
├── Does it need complex response?
│   ├── YES → Draft Response
│   └── NO → Continue
├── Is it a simple inquiry or request?
│   ├── YES → Reply to Sender
│   └── NO → Continue
└── Otherwise → Archive After Processing
```

## Priority Indicators

### High Priority Keywords:
- urgent, asap, emergency, immediate, today, deadline, critical, vital, essential

### Financial Indicators:
- payment, invoice, bill, cost, expense, budget, money, fund, charge, fee, price

### Security/Sensitive Indicators:
- confidential, private, password, login, account, security, breach, sensitive

### Need for Approval Indicators:
- contract, agreement, legal, terms, policy, HR, personnel, hiring, firing

## Automation Rules

1. **Direct Response Rule**: Simple math questions, factual inquiries → Auto-reply
2. **Approval Required Rule**: Payments over $X, vendor requests → Human approval
3. **Forwarding Rule**: Technical issues → IT team, HR matters → HR department
4. **Escalation Rule**: Escalate to human after 3 failed auto-responses
5. **Time-Based Rule**: Outside business hours → Acknowledge and schedule response

- Mark email status as 'read' after processing
- Move processed email files from Needs_Action to Done folder
- After processing email, update Dashboard.md with processing outcome
