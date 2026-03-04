## Setting Up Xero Credentials Guide

If you want the AI Employee to manage your accounting and financial data through Xero:

### 1. Create a Xero Account
1. Go to [https://www.xero.com/signup/](https://www.xero.com/signup/)
2. Sign up for a free account
3. Complete the registration process

### 2. Set Up Your Organization
You have two options:

**Option A: Use Demo Company (Recommended for Testing)**
1. After logging in, use the organization dropdown (top left)
2. Select "Demo Company (Global)" or create one if not available
3. This provides free access to Custom Connections for development

**Option B: Use Your Own Organization**
1. Create your own organization during signup
2. Note: Custom Connections cost $5-10/month for real organizations
3. Only available in AU, NZ, UK, and US regions

### 3. Access the Xero Developer Portal
1. Go to [https://developer.xero.com](https://developer.xero.com)
2. Log in with your Xero account credentials
3. Navigate to "My Apps"

### 4. Create a Custom Connection
1. Click "New app" or "Create app"
2. Fill in the app details:
   - **App name**: "AI Employee" (or any name you prefer)
   - **Integration type**: Custom Connection
   - **Company or application URL**: Your website or a placeholder URL
3. Click "Create" or "Save"

### 5. Configure Scopes
1. In your app's configuration page, select the required scopes:
    <details>
    <summary>Recommended Scopes (Click to expand)</summary>

    - ✓ `accounting.transactions.read`
    - ✓ `accounting.transactions`
    - ✓ `accounting.contacts.read`
    - ✓ `accounting.contacts`
    - ✓ `accounting.settings.read`
    - ✓ `accounting.settings`
    - ✓ `accounting.reports.read`
    - ✓ `accounting.reports.tenninetnine.read`
    - ✓ `accounting.budgets.read`
    - ✓ `accounting.journals.read`
    - ✓ `accounting.attachments`
    - ✓ `payroll.timesheets.read`
    - ✓ `payroll.timesheets`
    - ✓ `payroll.settings.read`
    - ✓ `payroll.settings`
    - ✓ `payroll.payslip.read`
    </details>
2. Click "Save" to save the scopes

### 6. Authorize the Connection
1. You should receive an authorization mail from Xero
2. Click the "Connect" link in the mail
3. You'll be redirected to a Xero authorization page
4. **Important**: Make sure you're connected to your Demo Company (Global) if using the free option
5. If you see "Subscription required to connect" for your organization, switch to Demo Company:
   - Go to [my.xero.com](https://my.xero.com)
   - Click on "Demo Company (Global)" to switch to it
   - Return to the authorization page and try again
6. Click "Allow access" to authorize the connection

### 7. Get Your Credentials
1. After successful authorization, go back to the Developer Portal
2. Navigate to your app's "Configuration" page
3. You should now see:
   - **Client id**: A long alphanumeric string
   - **Client secret 1**: Another long alphanumeric string
4. Click "Copy" next to each to copy them
5. **Important**: Copy the Client Secret immediately - you won't be able to see it again!

### 8. Set Environment Variables
Add your Xero credentials to the project's environment configuration:

1. **Open the .env file** in your project root directory with your preferred text editor:
   ```
   notepad .env        # Windows
   nano .env           # Linux/Mac
   ```

2. **Add your Xero credentials** to the file:
   ```
   XERO_CLIENT_ID=your_actual_client_id_here
   XERO_CLIENT_SECRET=your_actual_client_secret_here
   ```
   Replace `your_actual_client_id_here` and `your_actual_client_secret_here` with the values from step 7.

3. **Save the .env file**

4. **Run the sync script** to apply the changes:
   ```
   python scripts/sync_env_vars.py
   ```

This will:
- Set the variables permanently in your system (user-level environment variables)
- Make them available in the current terminal session
- Ensure the Xero MCP server can access these credentials

