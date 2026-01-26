# Quickstart: Silver Tier LinkedIn Automation & Scheduling

## Overview
This guide provides instructions for setting up and running the LinkedIn automation and scheduling system that posts business content twice weekly (Mondays and Thursdays).

## Prerequisites
- Python 3.13+
- Playwright browser automation library
- Access to LinkedIn account credentials
- Existing LinkedIn poster skill installed
- Cron (Linux/Mac) or Task Scheduler (Windows) access

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

2. Install Python dependencies:
```bash
pip install playwright
playwright install
```

3. Verify LinkedIn poster skill is available:
```bash
# Check that the LinkedIn poster skill is properly installed
# The skill should be located at .claude/skills/linkedin-poster/
```

## Configuration

1. Update the configuration file at `AI_Employee_Vault/config.json` with your LinkedIn credentials:
```json
{
  "linkedin": {
    "email": "your_linkedin_email@example.com",
    "password": "your_linkedin_password"
  },
  "content_generation": {
    "company_name": "Your Company Name",
    "industry": "Your Industry",
    "topics": ["business", "technology", "innovation"],
    "tone": "professional",
    "post_types": ["announcement", "insight", "success", "testimonial"]
  }
}
```

2. Ensure the following directories exist:
- `AI_Employee_Vault/Needs_Action/` - for scheduled post action files
- `AI_Employee_Vault/logs/` - for error and activity logs

## Setting up the Scheduler

### For Linux/Mac (cron):
1. Add the following cron job to run at 12 PM on Mondays and Thursdays:
```bash
# Edit crontab
crontab -e

# Add this line to schedule the LinkedIn post generator
0 12 * * 1,4 /path/to/python /path/to/linkedin_scheduler.py
```

### For Windows (Task Scheduler):
1. Create a scheduled task that runs at 12 PM on Mondays and Thursdays
2. Point the task to execute the LinkedIn scheduler script
3. Ensure the task runs with appropriate permissions

## Running the System

1. The system will automatically:
   - At 12 PM on Mondays and Thursdays, generate business-focused content
   - Create a post action file in the `Needs_Action` directory
   - The existing orchestrator will pick up the file and process it with the LinkedIn poster skill
   - The post will be scheduled for 6 PM publication on LinkedIn

2. Monitor the logs in `AI_Employee_Vault/logs/` for any errors or notifications

## Testing

1. To manually test the content generation:
```bash
python -m app.src.app.content_generator
```

2. To test the scheduler logic without waiting for the scheduled time:
```bash
python -c "from app.src.app.linkedin_scheduler import LinkedInScheduler; scheduler = LinkedInScheduler(); scheduler.generate_and_schedule_post()"
```

## Troubleshooting

- If posts are not appearing in the `Needs_Action` directory, check that the scheduler is running properly
- If LinkedIn authentication fails, verify credentials in the config file
- If posts are not being published, check the LinkedIn poster skill logs
- For credential errors, the system will notify you and store failed posts for manual retry

## Next Steps

- Monitor the system for the first few scheduled posts to ensure proper operation
- Adjust content generation parameters in the config file as needed
- Review published posts to ensure they meet your business objectives