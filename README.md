# Life Organizer

Automated personal life management system: email organization, iMessage relationship tracking, and proactive to-do generation.

## Features

- **Email Classification**: Automatically classify and organize Gmail messages
- **iMessage Integration**: Track conversations and flag messages needing response
- **To-Do Generation**: Auto-generate tasks from emails and texts
- **Google Sheets Dashboard**: Central hub for projects, relationships, and tasks
- **Nightly Automation**: Schedule daily processing via launchd

## Quick Start

```bash
# Setup
cd ~/Development/life-organizer
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure (see Configuration section)
cp config.example.py config.py
# Edit config.py with your settings

# Authenticate with Google
python auth_gmail.py

# Run tests
pytest tests/ -v

# Dry run - see what would happen without making changes
python dry_run.py 50 30  # 50 emails from last 30 days
```

## Prerequisites

1. **Python 3.9+**
2. **Google Cloud Project** with these APIs enabled:
   - Gmail API
   - Google Sheets API
   - Google Calendar API (optional)
   - People API (optional)
3. **OAuth2 Credentials** (Desktop app type)
4. **Google Service Account** (for Sheets access)
5. **Full Disk Access** for Terminal (required for iMessage)

## Configuration

### 1. Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable APIs: Gmail, Sheets, Calendar, People
4. Create OAuth2 credentials (Desktop app)
5. Download as `client_secret.json`
6. Create a Service Account for Sheets
7. Download as `service_account.json`

### 2. Google Sheet Setup

1. Create a new Google Sheet
2. Share it with your service account email
3. Create these tabs:
   - **To-Do**: Task tracking
   - **Projects**: Active and archived projects
   - **Relationships**: Contact CRM
   - **Questions**: Items needing review
   - **Processing Log**: Audit trail
   - **Dry Run**: Preview results

### 3. Configuration File

Copy `config.example.py` to `config.py` and fill in your values:

```python
# config.py
SHEET_ID = 'your-google-sheet-id'
SERVICE_ACCOUNT_FILE = '/path/to/service_account.json'
CLIENT_SECRET_FILE = '/path/to/client_secret.json'
```

### 4. iMessage Access (macOS only)

1. Open System Settings
2. Go to Privacy & Security → Full Disk Access
3. Add Terminal (or your terminal app)
4. Restart Terminal

## Usage

### Dry Run (Safe Preview)

```bash
# Preview 20 emails from last 30 days
python dry_run.py

# Preview 50 emails from last 60 days
python dry_run.py 50 60
```

### Manual Processing

```bash
# Dry run mode (default, safe)
python nightly.py

# With more emails
python nightly.py --emails=200 --days=14

# Live mode (use with caution!)
python nightly.py --live
```

### iMessage Only

```bash
python imessage_parser.py --days=30
```

## Nightly Automation

```bash
# Copy plist to LaunchAgents
cp com.life-organizer.nightly.plist ~/Library/LaunchAgents/

# Load the job
launchctl load ~/Library/LaunchAgents/com.life-organizer.nightly.plist

# Check status
launchctl list | grep life-organizer

# Unload
launchctl unload ~/Library/LaunchAgents/com.life-organizer.nightly.plist
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Gmail     │────▶│   Python    │────▶│  Dropbox    │
│   API       │     │   Service   │     │  (Optional) │
└─────────────┘     └──────┬──────┘     └─────────────┘
                          │
                    ┌─────▼─────┐
                    │  iMessage │
                    │  Database │
                    └─────┬─────┘
                          │
                    ┌─────▼─────┐
                    │  Google   │
                    │  Sheets   │
                    └───────────┘
```

### Key Files

| File | Purpose |
|------|---------|
| `config.py` | Your personal configuration (not committed) |
| `dry_run.py` | Preview classification without making changes |
| `nightly.py` | Main nightly processing job |
| `imessage_parser.py` | Parse iMessage database |
| `gmail_utils.py` | Gmail API wrapper |
| `sheets_utils.py` | Google Sheets operations |
| `db.py` | SQLite for tracking processed emails |
| `classify.py` | Email classification rules |

### Classification Categories

| Category | Action | Destination |
|----------|--------|-------------|
| `active_project` | Label in Gmail | `organized/active/{project}` |
| `archive_project` | Archive to Dropbox | `/Projects/{project}/Email/` |
| `personal` | Label in Gmail | `organized/personal` |
| `soft_delete` | Monthly zip | `/Archive/Email-Deleted/{YYYY-MM}.zip` |
| `needs_review` | Add to Questions tab | Manual review |

## Customization

### Adding Project Patterns

Edit `classify.py` to add your own project patterns:

```python
PROJECT_PATTERNS = {
    'active_project': {
        'example.com': 'My Project Name',
        'contractor@email.com': 'Renovation Project',
    },
    'archive_project': {
        'old-project.com': 'Archived Project',
    }
}
```

### Custom Classification Rules

Modify `quick_classify()` in `classify.py` to add rules for:
- Marketing emails (soft delete)
- Notifications (label only)
- Important senders (always keep)

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/test_classify.py -v
```

## Privacy

- All processing happens locally on your machine
- No data is sent to third parties (except Google APIs)
- Credentials are stored locally and never committed
- The `.gitignore` excludes all sensitive files

## License

MIT License - Use freely for personal projects.
