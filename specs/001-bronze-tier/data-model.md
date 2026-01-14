# Data Model: Bronze Tier - Personal AI Employee Foundation

## Entity: Task
- **Fields**:
  - id: Unique identifier for the task
  - title: Brief description of the task
  - description: Detailed description of what needs to be done
  - status: Current state (e.g., pending, in-progress, completed)
  - priority: Importance level (high, medium, low)
  - created_date: Timestamp when task was created
  - due_date: Optional deadline for task completion
  - assigned_to: Who the task is assigned to (AI Employee, human, etc.)

## Entity: Action Item
- **Fields**:
  - id: Unique identifier for the action item
  - task_id: Reference to the associated task
  - description: Detailed description of the specific action
  - required_approval: Whether human approval is needed
  - approval_status: Status of the approval process (pending, approved, rejected)
  - created_date: Timestamp when action item was created

## Entity: Dashboard
- **Fields**:
  - last_processed: Timestamp of last processing activity
  - active_tasks: Count of currently active tasks
  - pending_approvals: Count of items awaiting approval
  - recent_activity: List of recent actions taken
  - upcoming_tasks: List of scheduled tasks
  - proactive_suggestions: AI-generated suggestions for improvement

## Entity: Company Handbook
- **Fields**:
  - communication_guidelines: Rules for email and messaging
  - financial_guidelines: Policies for payments and invoicing
  - task_management_rules: Priority and approval procedures
  - escalation_procedures: When and how to escalate issues
  - working_hours_guidelines: Operating schedule and time zone considerations