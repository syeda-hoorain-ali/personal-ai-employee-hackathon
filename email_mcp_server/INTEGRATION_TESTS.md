# Email MCP Server Integration Tests

This document explains how to run integration tests that connect to actual email servers.

## Setup

1. **Copy the example configuration**:
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file** with your email credentials:
   - Set `ENABLE_INTEGRATION_TESTS=true`
   - Add your test email address to `TEST_EMAIL_ADDRESS`
   - Add your email password or app password to `TEST_EMAIL_PASSWORD` or `TEST_EMAIL_APP_PASSWORD`
   - Set `TEST_RECIPIENT` to an email address where you can receive test emails

3. **For Gmail users**, you'll need to use an App Password:
   - Go to Google Account settings
   - Enable 2-factor authentication
   - Generate an App Password for "Mail"
   - Use this App Password in the `TEST_EMAIL_APP_PASSWORD` field

### How to Get a Gmail App Password

To generate a Gmail App Password:

1. **Enable 2-Factor Authentication** (if not already enabled):
   - Go to [Google Account Settings](https://myaccount.google.com/)
   - Navigate to "Security"
   - Under "Signing in to Google," select "2-Step Verification"
   - Follow the steps to enable 2FA

2. **Generate an App Password**:
   - Go to [Google App Passwords Page](https://myaccount.google.com/apppasswords)
   - Sign in to your Google Account
   - Select "Mail" from the dropdown menu (for email applications)
   - Select the device you're using (or "Other" and name it "Email MCP Server")
   - Click "Generate"
   - **Important**: Google will generate a 16-character password (like: `abcd efgh ijkl mnop`)

3. **Use the App Password**:
   - Copy the 16-character app password
   - Put it in your `.env` file as `TEST_EMAIL_APP_PASSWORD`
   - Example: `TEST_EMAIL_APP_PASSWORD=abcdefghijklmnop` (without spaces)

4. **Update your .env file**:
   ```env
   TEST_EMAIL_ADDRESS=your-actual-gmail-address@gmail.com
   TEST_EMAIL_APP_PASSWORD=abcdefghijklmnop  # (without spaces)
   ENABLE_INTEGRATION_TESTS=true
   ```

**Note**: The app password will appear as 16 characters with spaces for readability, but when you put it in the .env file, you can include it with or without spaces - just make sure it's exactly 16 characters (excluding spaces).

This app password acts as a substitute for your regular Gmail password specifically for this application, allowing secure access without exposing your main account password.

## Running Integration Tests

To run all tests (including integration tests):
```bash
uv run pytest
```

To run only integration tests:
```bash
uv run pytest tests/email_mcp_server/integration/ -v
```

## Important Security Notes

⚠️ **Warning**: These integration tests will actually send emails and connect to email servers using your credentials.

- Only run these tests in a secure environment
- Never commit your `.env` file to version control
- Use a dedicated test email account
- Remember to set `ENABLE_INTEGRATION_TESTS=false` when not running tests

## Test Coverage

The integration tests verify:

- ✅ Connecting to email servers via SMTP and IMAP
- ✅ Sending actual emails
- ✅ Listing email folders
- ✅ Searching for emails
- ✅ Creating and managing draft emails
- ✅ All core functionality with real email providers

## Supported Email Providers

The integration tests work with:
- Gmail (with App Passwords)
- Outlook/Exchange
- Yahoo Mail
- Any provider supporting standard IMAP/SMTP

## Troubleshooting

If tests fail:
1. Verify your credentials are correct
2. Check if your email provider requires App Passwords
3. Ensure your firewall allows SMTP/IMAP connections
4. Verify the email address in `TEST_RECIPIENT` is valid
