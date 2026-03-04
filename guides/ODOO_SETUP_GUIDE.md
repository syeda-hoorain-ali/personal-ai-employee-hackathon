# Odoo Setup Guide for Personal AI Employee

**Complete beginner-friendly guide to installing and integrating Odoo Community Edition**

---

## Table of Contents

1. [What is Odoo?](#what-is-odoo)
2. [Installation Options](#installation-options)
   - [Option A: Installing Odoo on Windows  (Local)](#option-a-installing-odoo-on-windows-local)
   - [Option B: Deploying Odoo to Cloud (24/7)](#option-b-deploying-odoo-to-cloud-247)
3. [Additional Resources](#additional-resources)

---

## What is Odoo?

**Odoo** is a free, open-source business management software (ERP) that replaces multiple tools:

- **Accounting**: Invoices, expenses, payments, bank reconciliation
- **CRM**: Customer management, sales pipeline, leads
- **Inventory**: Stock management, warehouses, products
- **Projects**: Task tracking, timesheets, planning
- **E-commerce**: Online store, product catalog
- **HR**: Employees, payroll, time off

### Why Odoo for AI Employee?

Your AI can automatically:
- Create and send invoices when clients request them
- Track expenses and categorize transactions
- Manage customer contacts and relationships
- Generate financial reports for CEO briefings
- Record payments and reconcile accounts

**Example Workflow:**
```
Client WhatsApp: "Send me January invoice"
    ↓
AI reads Company_Handbook.md for rates
    ↓
AI creates draft invoice in Odoo
    ↓
AI writes approval file: Pending_Approval/accounting/INVOICE_Client_A.md
    ↓
You review in Odoo web interface
    ↓
You approve → Move file to Approved/
    ↓
AI posts invoice and sends via email
    ↓
Task moved to Done/accounting/
```

---

## Installation Options

You have three options for running Odoo:

### Option A: Local Installation (Windows)
- **Best for**: Testing and development
- **Cost**: Free
- **Availability**: Only when your computer is on
- **Setup time**: 30 minutes
- **Difficulty**: Easy
- **Use case**: Learning, testing, local development

### Option B: Odoo.com Cloud (Official SaaS)
- **Best for**: Quick start, no technical setup
- **Cost**: Starts at $24.90/user/month (Standard plan)
- **Availability**: 24/7
- **Setup time**: 5 minutes
- **Difficulty**: Very easy
- **Use case**: Production use, no server management
- **Note**: Community Edition not available on Odoo.com

### Option C: Self-Hosted Cloud (Oracle/AWS/DigitalOcean)
- **Best for**: 24/7 operation with full control
- **Cost**: Free (Oracle Cloud Free Tier) or $5-20/month
- **Availability**: 24/7
- **Setup time**: 1-2 hours
- **Difficulty**: Advanced (requires Linux knowledge)
- **Use case**: Platinum tier requirement, production use

**Recommendation**: Start with **Option A** (local) for testing, then move to **Option C** (self-hosted cloud) for 24/7 operation.

---

## Option A: Installing Odoo on Windows (Local)

### Step 1: Download Odoo

1. Visit: https://www.odoo.com/page/download
2. Click **"Community Edition"** (100% free)
3. Download **Windows installer** (odoo_19.0.latest.exe)
4. File size: ~1.5GB (includes PostgreSQL database)

### Step 2: Run the Installer
1. **Double-click** the downloaded .exe file
2. **User Account Control**: Click "Yes" to allow installation
3. **Installation Wizard**:
   - Click "Next"
   - Accept license agreement → "I Agree"
   - Installation directory: `C:\Program Files\Odoo 19.0` (default is fine)
   - **IMPORTANT**: Check ☑ "Install PostgreSQL" (required for database)
   - PostgreSQL password: Choose a strong password
     - Example: `MyOdoo2026!Secure`
     - **WRITE THIS DOWN** - you'll need it later
   - Click "Install"

4. **Wait 5-10 minutes** for installation to complete
5. When finished, Odoo will automatically open in your browser

### Step 3: Verify Installation

1. Browser should open automatically at: `http://localhost:8069`
2. If not, manually open browser and go to: `http://localhost:8069`
3. You should see the Odoo database creation screen

---

## Option B: Deploying Odoo to Cloud (24/7)

### Quick Cloud Setup with Odoo.com (5 minutes)

**Note**: Odoo.com offers Enterprise Edition (paid) with 15-day free trial. For free Community Edition with full API access, use local installation or self-hosted cloud (Oracle/DigitalOcean).

#### Step 1: Sign Up for Odoo.com

1. Go to: https://www.odoo.com/trial
2. Choose apps to install:
   - Select **Accounting**, **CRM**, **Employees**, **Invoicing**
   - Click **"Continue"**
3. Fill in your information:
   - **Name**: Your name
   - **Company Name**: Your business name
   - **Email**: Your email address
   - **Phone**: Your phone number
4. Click **Start now**
5. Activate your database:
   - Check your email for activation link
   - Fill in password and confirm password
   - Click **"Activate your database"**
6. Invite colleagues (optional):
   - Enter colleague names and emails
   - Click **"Send invites"** or **"Skip"**
7. Click **"Go to yourcompany.odoo.com"**

#### Step 2: Access Your Cloud Odoo

1. Your Odoo URL will be: `https://yourcompany.odoo.com`
2. Login with your email and password
3. You'll see the Odoo dashboard with installed apps

#### Step 3: Create API Key

1. Click profile icon → **"My Preferences"**
2. Navigate to **"Security"** tab
3. Generate API key:
   - Click **"Add API Key"**
   - Enter your password
   - Click **"Confirm Password"**
4. Configure the key:
   - Description: `MCP Server Access`
   - Duration: Select **"3 months"** (or your preferred duration)
   - Click **"Generate key"**

5. **Copy the API key immediately ans store it securely** (you won't be able to see it again)

#### Step 4: Update .env File

Add these configuration values to your `.env` file in the project root:

```env
# Odoo Configuration (Odoo.com Cloud)
ODOO_URL=https://yourcompany.odoo.com
ODOO_DB=yourcompany
ODOO_USER=your-email@example.com
ODOO_API_KEY=your_odoo_api_key_here
ODOO_YOLO=read
```

**Replace the following**:
- `yourcompany` - Your actual company subdomain
- `your-email@example.com` - Your Odoo login email
- `your_odoo_api_key_here` - The API key you copied in Step 3

**Important Limitations**:
- ⚠️ Free trial lasts 15 days
- ⚠️ After trial: $24.90/user/month
- ⚠️ Enterprise Edition (not Community)
- ⚠️ Limited API access compared to self-hosted

**For free 24/7 Odoo**: Use Oracle Cloud Free Tier (see detailed guide in project docs) or start with local installation for testing.

---

## Additional Resources

- **Odoo Documentation**: https://www.odoo.com/documentation/19.0/
- **Odoo Community Forum**: https://www.odoo.com/forum
- **MCP Server GitHub**: https://github.com/ivnvxd/mcp-server-odoo
- **Odoo API Reference**: https://www.odoo.com/documentation/19.0/developer/reference/external_api.html

---

**Last Updated**: 2026-02-27
**Odoo Version**: 19.0 Community Edition
**MCP Server**: mcp-server-odoo (ivnvxd)
