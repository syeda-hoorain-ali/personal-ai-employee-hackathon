## Setting Up Google Credentials (Optional)

If you want the AI Employee to monitor your Gmail account:

### 1. Create a Google Cloud Project
1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" at the top, then "New Project"
3. Give your project a name (e.g., "AI Employee") and click "Create"

### 2. Enable Gmail API
1. In your project dashboard, search for "Gmail API"
2. Click on "Gmail API" and then "Enable"

### 3. Configure Consent Screen
1. In the left sidebar, click "APIs & Services" > "OAuth Consent Screen"
2. Click "Configure Consent Screen"
3. If prompted with "Google Auth Platform not configured yet", click "Get Started"
4. Fill in the application information:
   - Application name: "AI Employee"
   - User support email: your email
5. Click "Next"
6. Select "External" and click "Next"
7. Fill in the application information:
   - Contact information: your email
8. Click "Next"
9. Check the "I agree" checkbox and click "Continue"
10. Click "Create"

### 4. Create OAuth 2.0 Credentials

1. From the OAuth overview page, click "Create OAuth Client"
2. If prompted with "OAuth consent screen not configured", click "Configure Consent Screen" and follow the steps in section 3 above
3. Select "Application type" as "Desktop application"
4. Give it a name (e.g., "AI Employee Desktop App")
5. Click "Create"
6. Download the credentials file and rename it to `gcp-oauth.keys.json` in the `~/.gmail-mcp/` directory

### 5. Add Your Email as a Test User
1. After creating the OAuth credentials, go back to "APIs & Services" > "OAuth consent screen" > "Audience"
2. Under the "Test users" section, click "Add users"
3. Add your email address that you'll use to authenticate
4. Click "Save" to save the changes

### 6. Place the Credentials File
- Create the `~/.gmail-mcp/` directory and copy the `gcp-oauth.keys.json` file to it
