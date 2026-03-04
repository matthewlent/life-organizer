# Life Organizer Setup Guide for Leon

This guide assumes you've never used Terminal before. Follow each step exactly.

---

## Part 1: Opening Terminal

**Terminal** is an app on your Mac that lets you type commands. Here's how to open it:

1. Press **Command (⌘) + Space** to open Spotlight search
2. Type **Terminal**
3. Press **Enter**

A white or black window will open with a blinking cursor. This is Terminal.

**Tip:** Right-click the Terminal icon in your Dock and select "Options → Keep in Dock" so you can find it easily later.

---

## Part 2: Install Homebrew

Homebrew is a tool that helps you install other tools. Copy and paste this command into Terminal and press Enter:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**What will happen:**
- It will ask for your Mac password (the one you use to log in)
- When you type your password, you won't see any characters appear - that's normal, just type it and press Enter
- It will take a few minutes to install
- Follow any instructions it shows at the end

**Important:** After installation, it may show some commands to run. They look like this:
```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

If you see these, copy and paste each line into Terminal and press Enter.

---

## Part 3: Install Required Tools

Now install the tools you need. Copy and paste each command, one at a time, pressing Enter after each:

```bash
brew install git
```

Wait for it to finish, then:

```bash
brew install gh
```

Wait for it to finish, then:

```bash
brew install python@3.11
```

Wait for it to finish, then:

```bash
brew install node
```

---

## Part 4: Log into GitHub

GitHub is where the code is stored. Run this command:

```bash
gh auth login
```

You'll see a series of questions. Here's what to select:

1. **"What account do you want to log into?"**
   - Use arrow keys to select **GitHub.com**
   - Press Enter

2. **"What is your preferred protocol?"**
   - Select **HTTPS**
   - Press Enter

3. **"Authenticate Git with your GitHub credentials?"**
   - Select **Yes**
   - Press Enter

4. **"How would you like to authenticate?"**
   - Select **Login with a web browser**
   - Press Enter

5. It will show a code like `XXXX-XXXX`
   - Copy this code
   - Press Enter to open your browser
   - Paste the code on the GitHub website
   - Click "Authorize"

When you see "Authentication complete" in Terminal, you're done!

---

## Part 5: Install Claude Code

Claude Code is the AI assistant that will help you. Run:

```bash
npm install -g @anthropic-ai/claude-code
```

This may take a minute. When it's done, you'll see your cursor again.

---

## Part 6: Download the Project

Create a folder for your projects and download the code:

```bash
mkdir -p ~/Development
```

```bash
cd ~/Development
```

```bash
gh repo clone matthewlent/life-organizer
```

```bash
cd life-organizer
```

---

## Part 7: Set Up Python

Run these commands one at a time:

```bash
python3 -m venv venv
```

```bash
source venv/bin/activate
```

You should now see `(venv)` at the beginning of your Terminal line. This means you're in the project's Python environment.

```bash
pip install -r requirements.txt
```

This installs the required Python packages. It may take a minute.

---

## Part 8: Enable iMessage Access

For the app to read your iMessages, you need to give Terminal permission:

1. Click the **Apple menu ()** in the top-left corner
2. Click **System Settings**
3. Click **Privacy & Security** in the left sidebar
4. Scroll down and click **Full Disk Access**
5. Click the **+** button
6. Navigate to **Applications → Utilities → Terminal**
7. Select Terminal and click **Open**
8. Toggle the switch ON for Terminal
9. **Quit Terminal completely** (Command+Q)
10. **Reopen Terminal**

---

## Part 9: Launch Claude Code

Now let's have Claude Code help you set up the Google services:

1. Open Terminal (if not already open)

2. Navigate to the project folder:
```bash
cd ~/Development/life-organizer
```

3. Activate the Python environment:
```bash
source venv/bin/activate
```

4. Launch Claude Code:
```bash
claude
```

5. When Claude Code starts, copy and paste this message to it:

```
Hi Claude! I'm Leon and I need help setting up this Life Organizer project.

I'm using Google Workspace with bracely.ai as my domain.

Please help me step by step to:
1. Create a Google Cloud project
2. Enable the Gmail, Sheets, and Calendar APIs
3. Create OAuth2 credentials (Desktop app type)
4. Create a service account for Sheets
5. Create a Google Sheet with the required tabs (To-Do, Projects, Relationships, etc.)
6. Save the credential files to this project folder
7. Create my config.py file with the correct paths
8. Run the Gmail authentication
9. Test that everything works

Please go slowly and wait for me to complete each step before moving on.
```

Claude Code will then guide you through each step interactively!

---

## Part 10: What Claude Code Will Help You Do

Here's an overview of what you'll be setting up (Claude will guide you through the details):

### Google Cloud Project
- Go to console.cloud.google.com
- Create a new project called "Life Organizer"
- Enable APIs (Gmail, Sheets, Calendar)

### Credentials
- Create an "OAuth 2.0 Client ID" (for Gmail access)
- Create a "Service Account" (for Sheets access)
- Download both as JSON files

### Google Sheet
- Create a new Google Sheet
- Share it with the service account
- Add tabs: To-Do, Projects, Relationships, Questions, Processing Log, Dry Run

### Config File
- Create config.py with your settings
- Run the authentication
- Test everything works

---

## Part 11: Daily Usage (After Setup)

Once everything is set up, here's how to use it day to day:

### Open the project:
```bash
cd ~/Development/life-organizer
source venv/bin/activate
```

### Preview what the system would do (safe, no changes):
```bash
python dry_run.py 50 30
```
This looks at 50 emails from the last 30 days.

### Check your iMessages for items needing response:
```bash
python imessage_parser.py --days=14
```

### Run the full system (dry run first!):
```bash
python nightly.py
```

### Run with actual changes (be careful!):
```bash
python nightly.py --live
```

### Get help from Claude Code anytime:
```bash
claude
```

---

## Troubleshooting

### "command not found: brew"
Close Terminal, reopen it, and try the Homebrew installation command again.

### "command not found: gh"
Run: `brew install gh`

### "Permission denied" or "Access denied" for iMessages
Make sure you completed Part 8 (Full Disk Access) and restarted Terminal.

### Password not appearing when typing
This is normal! Mac hides passwords. Just type it and press Enter.

### "Token has been expired or revoked"
Run these commands:
```bash
cd ~/Development/life-organizer
rm gmail_token.json
source venv/bin/activate
python auth_gmail.py
```

### Something else not working?
Launch Claude Code and describe what's happening:
```bash
cd ~/Development/life-organizer
source venv/bin/activate
claude
```

Then tell Claude what error you're seeing.

---

## Quick Reference Card

Save these commands somewhere handy:

| What you want to do | Command |
|---------------------|---------|
| Open project folder | `cd ~/Development/life-organizer` |
| Activate Python | `source venv/bin/activate` |
| Preview emails | `python dry_run.py 50 30` |
| Check iMessages | `python imessage_parser.py --days=14` |
| Run nightly job | `python nightly.py` |
| Get help | `claude` |

---

## Need Help?

1. **First choice:** Run `claude` in the project folder and ask for help
2. **Second choice:** Text Matt

Good luck! 🚀
