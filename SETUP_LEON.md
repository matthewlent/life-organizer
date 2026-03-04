# Setup Guide for Leon

This guide will walk you through setting up the Life Organizer project from scratch on your Mac, using Claude Code to help with configuration.

## Prerequisites

- macOS (for iMessage integration)
- A Google Workspace account (bracely.ai)
- About 30 minutes for initial setup

---

## Step 1: Install Homebrew (if not already installed)

Open Terminal and run:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow the prompts. After installation, run the commands it shows to add Homebrew to your PATH.

---

## Step 2: Install Git and GitHub CLI

```bash
# Install git and GitHub CLI
brew install git gh

# Authenticate with GitHub
gh auth login
```

When prompted:
- Select **GitHub.com**
- Select **HTTPS**
- Select **Login with a web browser**
- Copy the code shown and press Enter
- Complete authentication in your browser

---

## Step 3: Install Python 3

```bash
# Install Python 3
brew install python@3.11

# Verify installation
python3 --version
```

---

## Step 4: Install Claude Code

```bash
# Install Claude Code globally
npm install -g @anthropic-ai/claude-code

# Or if you don't have npm, install Node.js first:
brew install node
npm install -g @anthropic-ai/claude-code
```

---

## Step 5: Clone the Repository

```bash
# Create a Development folder (if you don't have one)
mkdir -p ~/Development
cd ~/Development

# Clone the repo
gh repo clone matthewlent/life-organizer

# Enter the directory
cd life-organizer
```

---

## Step 6: Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 7: Launch Claude Code for Setup

Now let Claude Code help you set up the Google integrations:

```bash
# Make sure you're in the project directory
cd ~/Development/life-organizer

# Launch Claude Code
claude
```

Once Claude Code is running, say:

> "Help me set up this Life Organizer project. I need to:
> 1. Create a Google Cloud project for bracely.ai (my Google Workspace)
> 2. Enable Gmail, Sheets, and Calendar APIs
> 3. Create OAuth2 credentials for the desktop app
> 4. Create a service account for Sheets access
> 5. Create a new Google Sheet with the required tabs
> 6. Configure config.py with my credentials
> 7. Test the authentication"

Claude Code will guide you through each step interactively.

---

## Step 8: Google Cloud Setup (Overview)

Claude Code will help, but here's what you'll be doing:

### 8.1 Create Google Cloud Project
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Sign in with your bracely.ai account
3. Create a new project (e.g., "Life Organizer")

### 8.2 Enable APIs
Enable these APIs in your project:
- Gmail API
- Google Sheets API
- Google Calendar API
- People API (for contacts)

### 8.3 Create OAuth2 Credentials
1. Go to APIs & Services → Credentials
2. Create Credentials → OAuth client ID
3. Application type: **Desktop app**
4. Download the JSON file
5. Save as `client_secret.json` in the project folder

### 8.4 Create Service Account (for Sheets)
1. Go to APIs & Services → Credentials
2. Create Credentials → Service Account
3. Download the JSON key
4. Save as `service_account.json` in the project folder

### 8.5 Create Google Sheet
1. Create a new Google Sheet
2. Name it "Life Organizer"
3. Share it with the service account email (ends in `@*.iam.gserviceaccount.com`)
4. Copy the Sheet ID from the URL

---

## Step 9: Configure the Project

Copy the example config and edit it:

```bash
cp config.example.py config.py
```

Then edit `config.py` with your values:

```python
SHEET_ID = 'your-sheet-id-from-url'
SERVICE_ACCOUNT_FILE = '/Users/leon/Development/life-organizer/service_account.json'
CLIENT_SECRET_FILE = '/Users/leon/Development/life-organizer/client_secret.json'
```

---

## Step 10: Authenticate with Gmail

```bash
# Make sure venv is activated
source venv/bin/activate

# Run authentication
python auth_gmail.py
```

A browser window will open. Log in with your bracely.ai account and grant permissions.

---

## Step 11: Enable iMessage Access

1. Open **System Settings**
2. Go to **Privacy & Security → Full Disk Access**
3. Click **+** and add **Terminal** (or iTerm if you use that)
4. Restart Terminal

Test it:
```bash
python imessage_parser.py --days=7
```

---

## Step 12: Test the Setup

```bash
# Run a dry run to test everything
python dry_run.py 10 7
```

This will classify 10 emails from the last 7 days and log results to your Google Sheet.

---

## Step 13: Commit Your Configuration

Your credential files are already in `.gitignore`, so they won't be committed. But you can commit any customizations to `classify.py` or other files:

```bash
# Check what's changed
git status

# If you've customized classify.py with your own patterns:
git add classify.py

# Commit
git commit -m "Add custom classification patterns for bracely.ai"

# Push to your own fork (optional - create fork first)
gh repo fork --clone=false
git push origin main
```

---

## Step 14: Set Up Nightly Automation (Optional)

Edit the plist file to use your paths:

```bash
# Edit the plist
nano com.life-organizer.nightly.plist
```

Replace `YOUR_USERNAME` with `leon` (or your actual username).

Then install:

```bash
# Copy to LaunchAgents
cp com.life-organizer.nightly.plist ~/Library/LaunchAgents/

# Load it
launchctl load ~/Library/LaunchAgents/com.life-organizer.nightly.plist

# Check status
launchctl list | grep life-organizer
```

---

## Troubleshooting

### "Token has been expired or revoked"
```bash
rm gmail_token.json
python auth_gmail.py
```

### "Access denied" for iMessage
Make sure Terminal has Full Disk Access (Step 11).

### "Service account file not found"
Check the path in `config.py` matches where you saved the file.

### Google Sheet not updating
Make sure you shared the sheet with the service account email.

---

## Daily Usage

```bash
# Activate environment
cd ~/Development/life-organizer
source venv/bin/activate

# Dry run (preview)
python dry_run.py 50 30

# Check iMessages
python imessage_parser.py --days=14

# Full nightly run (dry)
python nightly.py

# Full nightly run (live - makes changes)
python nightly.py --live
```

---

## Getting Help

In the project directory, run:
```bash
claude
```

Then ask Claude Code anything about the project!

---

## Files You'll Create

| File | Purpose | Committed to Git? |
|------|---------|-------------------|
| `config.py` | Your personal configuration | No (gitignored) |
| `client_secret.json` | OAuth2 credentials | No (gitignored) |
| `service_account.json` | Sheets access | No (gitignored) |
| `gmail_token.json` | Auth token (auto-created) | No (gitignored) |
| `life_organizer.db` | Local database | No (gitignored) |
