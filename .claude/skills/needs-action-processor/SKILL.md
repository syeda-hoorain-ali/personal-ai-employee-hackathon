---
name: needs-action-processor
description: Process files in the Needs_Action folder according to Company Handbook rules. Use this skill when you need to handle tasks placed in the Needs_Action directory by watchers, following the rules defined in the Company Handbook.
---

# Needs Action Processor

Process files in the Needs_Action folder by analyzing intent, creating structured plans, and following Company Handbook rules. Use this skill when you need to handle tasks placed in the Needs_Action directory by watchers, following the rules defined in the Company Handbook.

## When to Use This Skill

Use this skill when:
- There are files in the Needs_Action folder that need processing
- You need to apply Company Handbook rules to incoming tasks
- Watchers have placed files in Needs_Action that require action
- You need to create structured plan files with checkboxes for complex tasks

## How to Use This Skill

1. Check the Needs_Action folder for pending files
2. Read and analyze the file content to understand the intent
3. Create a plan file in the Plans folder with the name `{original_filename}.plan.md`
4. The plan file will contain checkboxes for tracking progress based on the detected intent
5. Apply Company Handbook rules to determine if approval is needed
6. Move processed files to appropriate folders (Done, Pending_Approval, etc.)
7. Add log entry to the Logs folder with timestamp and action details
8. Update the Dashboard with processing outcomes

## Files and Directories

- `<vault>/Needs_Action/` - Contains files waiting for processing
- `<vault>/Plans/` - Contains generated plan files with checkboxes for tracking progress
- `<vault>/Company_Handbook.md` - Rules for processing tasks
- `<vault>/Dashboard.md` - Log of completed actions
- `<vault>/Done/` - Successfully processed files
- `<vault>/Pending_Approval/` - Files awaiting human approval
- `<vault>/Logs/` - Audit logs in YYYY-MM-DD.json format

## Plan Creation Template

When processing files, the skill creates plan files using the template in `./template/process_plan_template.md` with the following structure:
- **Understanding the Intent**: Checkboxes to confirm comprehension of the task
- **Action Plan**: Specific actions based on detected intent with checkboxes
- **Approval Requirements**: Checkboxes for approval-related tasks
- **Execution Steps**: Steps for processing the file with checkboxes
- **Completion Verification**: Final verification steps with checkboxes

## Company Handbook Rule Processing

The script analyzes each file and applies rules based on the Company Handbook:

- **Financial Guidelines**: Payments over $100 require approval - moves to Pending_Approval
- **Communication Guidelines**: Professional and courteous communications
- **Task Management**: Prioritize urgent items marked with 'urgent', 'asap', 'emergency', etc.
- **Custom Rules**: Any specific rules defined in your Company Handbook

The processing logic will:
1. Read the Company Handbook from `<vault>/Company_Handbook.md`
2. Parse rules based on headers like "Financial Guidelines", "Communication Guidelines", etc.
3. Apply relevant rules based on content analysis
4. Take appropriate actions (move to Done, Pending Approval, etc.)
5. Log decisions in the Dashboard for transparency

## File Processing Workflow

For each file in Needs_Action folder, follows this complete workflow:

1. **Analyze**: Read the file content and identify the type of task
2. **Understand Intent**: Analyze the content to understand the intent and required actions
3. **Plan**: Create a plan file in the Plans folder with the name `<vault>/Plans/{original_filename}.plan.md` containing checkboxes for tracking progress
4. **Apply Rules**: Consult Company Handbook for appropriate action and approval requirements
5. **Execute**: Perform required action using available tools
   - For email files, follow the [Email Processing Reference Guide](./references/email_processing_guide.md) to determine the appropriate response (reply, forward, request approval, etc.)
6. **Move File**: Move the original file to appropriate folder
   - If Done move it to `<vault>/Done` folder
   - If human approval needed move it to `<vault>/Pending_Approval` folder
7. **Update**: Log the action in Dashboard and update status appropriately
8. **Log**: Create JSON log entry in Logs folder with required fields

## Processing Capabilities

The script analyzes each file and applies rules based on the Company Handbook to:
1. Read and analyze files in the Needs_Action folder
2. Understand the intent and create structured plan files with checkboxes
3. Apply Company Handbook rules to determine appropriate actions
4. Process email files according to the [Email Processing Reference Guide](./references/email_processing_guide.md)
5. Move processed files appropriately (to Done, Pending_Approval, etc.)
6. Update the Dashboard with processing outcomes
7. Add JSON log entries to track actions taken with required fields:
   - timestamp
   - action_type
   - actor
   - target
   - parameters
   - approval_status
   - approved_by
   - result
