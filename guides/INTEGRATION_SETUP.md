# Integration Setup Guide

Connect MuBot to Google Sheets or Notion for automated email campaigns.

---

## 📊 Option 1: Google Sheets (Recommended - Easier)

### Step 1: Create Your Sheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new spreadsheet called "Job Applications"
3. Add these column headers in row 1:

| Company | Role | Recipient Name | Email | Job Description | Status | Last Contact | Notes |
|---------|------|----------------|-------|-----------------|--------|--------------|-------|

### Step 2: Add Job Data

Fill in your job applications:

| Company | Role | Recipient Name | Email | Job Description | Status | Last Contact | Notes |
|---------|------|----------------|-------|-----------------|--------|--------------|-------|
| Netflix | Data Scientist | Sarah Chen | sarah@netflix.com | [Paste full JD] | Pending | | |
| Google | ML Engineer | | | [Paste full JD] | Pending | | No email yet |
| Stripe | Data Engineer | John Doe | john@stripe.com | [Paste full JD] | Pending | | |

### Step 3: Set Up Google Cloud Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable the **Google Sheets API**:
   - Go to "APIs & Services" → "Library"
   - Search "Google Sheets API"
   - Click "Enable"

4. Enable the **Google Drive API** (for reading the sheet):
   - Search "Google Drive API"
   - Click "Enable"

5. Create a Service Account:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "Service Account"
   - Name: "mubot-sheets"
   - Click "Create and Continue"
   - Skip optional steps, click "Done"

6. Create a Key:
   - Click on your service account
   - Go to "Keys" tab
   - Click "Add Key" → "Create New Key"
   - Choose JSON format
   - Click "Create"
   - **Download the JSON file**

7. Rename and move the file:
   ```bash
   mv ~/Downloads/your-project-*.json ./credentials/sheets_credentials.json
   ```

### Step 4: Share Your Sheet

1. Open your Google Sheet
2. Click "Share" button (top right)
3. Add the service account email:
   - It looks like: `mubot-sheets@your-project.iam.gserviceaccount.com`
   - Give "Editor" access
   - Click "Send"

### Step 5: Test Connection

```bash
cd /path/to/mubot
source venv/bin/activate

# Test reading from sheets
python -c "
import asyncio
from integrations.google_sheets import GoogleSheetsIntegration

async def test():
    sheets = GoogleSheetsIntegration()
    jobs = await sheets.get_pending_jobs()
    print(f'Found {len(jobs)} pending jobs')
    for job in jobs:
        print(f'  - {job[\"company\"]}: {job[\"role\"]}')

asyncio.run(test())
"
```

---

## 📝 Option 2: Notion (More Structured)

### Step 1: Create Notion Database

1. Go to [Notion](https://notion.so)
2. Create a new page called "Job Applications"
3. Add a database with these properties:

| Property | Type | Notes |
|----------|------|-------|
| Company | Title | Primary identifier |
| Role | Text | Job title |
| Recipient Name | Text | Who to email |
| Email | Email | Recipient's email |
| Job Description | Text | Full JD |
| Status | Select | Options: Pending, Sent, Replied, No Response, Dead |
| Last Contact | Date | When last emailed |
| Follow-up Count | Number | How many follow-ups sent |
| Notes | Text | Any additional info |

### Step 2: Get Notion Integration Token

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click "New Integration"
3. Name: "MuBot"
4. Associated workspace: Your workspace
5. Capabilities: Check "Read content" and "Update content"
6. Click "Submit"
7. **Copy the "Internal Integration Token"**

8. Add to your `.env`:
   ```bash
   NOTION_API_TOKEN=secret_xxx_your_token_here
   ```

### Step 3: Get Database ID

1. Open your Job Applications database in Notion
2. Look at the URL: `https://www.notion.so/your-workspace/xxx-xxx-xxx?v=...`
3. The database ID is the part between the last `/` and `?`
4. **Copy this ID**

5. Add to your `.env`:
   ```bash
   NOTION_DATABASE_ID=xxx-xxx-xxx
   ```

### Step 4: Connect Integration to Database

1. Go back to your Notion database
2. Click the "..." menu (top right)
3. Click "Add connections"
4. Search for "MuBot" and select it
5. Click "Confirm"

### Step 5: Test Connection

```bash
cd /path/to/mubot
source venv/bin/activate

# Test reading from Notion
python -c "
import asyncio
from integrations.notion_integration import NotionIntegration
from mubot.config import get_settings

async def test():
    settings = get_settings()
    notion = NotionIntegration(
        token=settings.notion_api_token,
        database_id=settings.notion_database_id
    )
    jobs = await notion.get_pending_jobs()
    print(f'Found {len(jobs)} pending jobs')
    for job in jobs:
        print(f'  - {job[\"company\"]}: {job[\"role\"]}')

asyncio.run(test())
"
```

---

## 🚀 Running Automated Campaigns

### Preview Mode (Dry Run)

Test without sending emails:

```bash
# For Google Sheets
python auto_campaign.py --source sheets --limit 3 --dry-run

# For Notion
python auto_campaign.py --source notion --limit 3 --dry-run
```

### Send Emails

Run for real (will ask for confirmation before each send):

```bash
python auto_campaign.py --source sheets --limit 5
```

### Check Follow-ups Only

```bash
python auto_campaign.py --followups-only
```

### Check for Replies (Automated Response Tracking)

```bash
# Check for replies once
python auto_campaign.py --check-replies

# Or use the standalone script
python scripts/schedule_replies.py
```

---

## 📅 Scheduling Automatic Runs

### Using Cron (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add these lines:

# 1. Check for replies every hour (automated response tracking)
# This cancels follow-ups when people reply
0 * * * * cd /path/to/mubot && python auto_campaign.py --check-replies >> /path/to/mubot/logs/replies.log 2>&1

# 2. Run campaign every weekday at 9 AM (send pending emails)
0 9 * * 1-5 cd /path/to/mubot && python auto_campaign.py --source sheets --limit 3 >> /path/to/mubot/logs/campaign.log 2>&1

# 3. Send due follow-ups at 10 AM
0 10 * * 1-5 cd /path/to/mubot && python auto_campaign.py --followups-only >> /path/to/mubot/logs/followups.log 2>&1
```

**What this does:**
1. **Hourly**: Checks Gmail for replies → Auto-cancels follow-ups for respondents
2. **9 AM**: Sends pending initial emails from your sheet
3. **10 AM**: Sends due follow-ups (only if no reply received)

### Using launchd (Mac alternative)

Create `~/Library/LaunchAgents/com.mubot.campaign.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.mubot.campaign</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/mubot/venv/bin/python</string>
        <string>/path/to/mubot/auto_campaign.py</string>
        <string>--source</string>
        <string>sheets</string>
        <string>--limit</string>
        <string>3</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
        <key>Weekday</key>
        <integer>1</integer> <!-- Monday -->
    </dict>
    <key>WorkingDirectory</key>
    <string>/path/to/mubot</string>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.mubot.campaign.plist
```

---

## 🔧 Follow-Up Schedule

MuBot schedules 3 follow-ups automatically:

| Follow-up | Timing | Purpose |
|-----------|--------|---------|
| **#1** | 4 working days | Gentle reminder |
| **#2** | 8 working days | Add value/context |
| **#3** | 10 working days | Final attempt |

**Working days** = Monday-Friday (skips weekends)

Example:
- **Day 0 (Monday)**: Initial email sent
- **Day 4 (Friday)**: Follow-up #1
- **Day 8 (Tuesday)**: Follow-up #2
- **Day 10 (Thursday)**: Follow-up #3

---

## 📝 Tips

### Google Sheets Tips

- Use "Data Validation" for Status column to avoid typos
- Use "Wrap text" for Job Description column
- Color-code rows by status (green = sent, yellow = replied, red = no response)

### Notion Tips

- Create different views: Kanban (by Status), Calendar (by Last Contact)
- Use templates for new job entries
- Set up Slack notifications when Status changes

### General Tips

- Start with `--dry-run` to preview before sending
- Check `data/heartbeat-state.json` for scheduled follow-ups
- Review `logs/` for campaign history

---

## 🆘 Troubleshooting

### "Credentials file not found"
- Make sure `sheets_credentials.json` is in `./credentials/`
- Check file permissions

### "Spreadsheet not found"
- Verify the sheet name matches exactly
- Check that service account has access

### "Notion API error"
- Verify token is correct
- Check database ID is correct
- Ensure integration is connected to database

### Emails not sending
- Check daily limit not exceeded
- Verify Gmail credentials are valid
- Check `.env` has correct settings

---

## ✅ Quick Checklist

**For Google Sheets:**
- [ ] Created spreadsheet with correct columns
- [ ] Enabled Sheets API and Drive API
- [ ] Created service account
- [ ] Downloaded JSON credentials
- [ ] Shared sheet with service account
- [ ] Tested connection

**For Notion:**
- [ ] Created database with correct properties
- [ ] Created integration
- [ ] Copied integration token
- [ ] Copied database ID
- [ ] Connected integration to database
- [ ] Tested connection

---

**Need help?** Open an issue with your error message!
