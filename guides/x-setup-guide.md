# X MCP Server - Enhanced Edition
## 📋 Prerequisites

Before you begin, you'll need:

1. An X Developer Account (sign up at [developer.x.com](https://developer.x.com))
2. An X App created in the Developer Portal
3. API credentials (detailed setup below)
4. Node.js 18+ installed

## 🔐 Authentication Setup

### Setting Up Your X App

1. **Create a Developer Account**:
   - Go to [developer.x.com](https://developer.x.com)
   - Sign in with your Twitter account
   - Apply for developer access if you haven't already

2. **Create a New App**:
   - Navigate to the [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
   - Click "Projects & Apps" → "New Project"
   - Give your project a name
   - Select your use case
   - Create a new App within the project

3. **Configure App Permissions**:
   - In your app settings, go to "User authentication settings"
   - Click "Set up"
   - Set App permissions to "Read and write and Direct message"
   - Set Type of App to "Web App, Automated App or Bot"
   - Add Callback URLs: `http://localhost:3000/callback`
   - Set Website URL (can be your GitHub repo)

5. **Get Your Client Credentials**:
   - Copy Client ID and Client Secret
   - Save these for the next step

6. **Set Environment Variables**:
   Add your X credentials to the project's environment configuration:

   a. **Open the .env file** in your project root directory:
      ```
      notepad .env        # Windows
      nano .env           # Linux/Mac
      ```

   b. **Add your X credentials** to the file:
      ```
      X_CLIENT_ID=your_actual_client_id_here
      X_CLIENT_SECRET=your_actual_client_secret_here
      ```
      Replace with the values from step 5.

   c. **Save the .env file**

   d. **Run the sync script** to apply the changes:
      ```
      python scripts/sync_env_vars.py
      ```

   This will set the variables permanently in your system and make them available for the X MCP server.

7. **Generate User Tokens**:
   ```bash
   # Run the OAuth2 setup script
   node scripts/oauth2-setup.js
   ```
