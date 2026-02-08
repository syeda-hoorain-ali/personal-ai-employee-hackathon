## Setting Up LinkedIn Credentials (Optional)

If you want the AI Employee to automatically post on LinkedIn:

### 1. Create the Config File
1. Navigate to the `AI_Employee_Vault` directory in your project
2. Create a file named `config.json` in this directory
3. The file structure should be: `AI_Employee_Vault/config.json`

### 2. Add Your LinkedIn Credentials
1. Open the `config.json` file in a text editor
2. Add your LinkedIn email and password in the following format:

```
{
  "linkedin": {
    "email": "YOUR_LINKEDIN_EMAIL",
    "password": "YOUR_LINKEDIN_PASSWORD"
  }
}
```

### 3. Security Note
⚠️ **Warning**: Storing credentials in plain text is a security risk. Consider the following:
- Use a strong, unique password for your LinkedIn account
- Do not commit this file to version control (it should be in your `.gitignore`)
- Consider using a dedicated LinkedIn account for automation
- Change your password regularly

### 4. Configure LinkedIn Auto-Posting
The system includes a LinkedIn poster script that can automatically post updates:
1. The script is located at `app/scripts/linkedin_poster_cli.py`
2. To schedule automatic posts, run the setup script as administrator:
   ```
   python scripts/setup.py
   ```
3. When prompted, ensure you run with administrator privileges to enable the scheduled task
4. The system will post daily at 12:00 PM if credentials are properly configured
