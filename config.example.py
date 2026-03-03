#!/usr/bin/env python3
"""
Configuration template for Life Organizer.
Copy this file to config.py and fill in your values.
"""

# Google Sheet ID (from the URL: docs.google.com/spreadsheets/d/SHEET_ID/...)
SHEET_ID = 'your-google-sheet-id-here'

# Path to your Google Service Account JSON file
# Create at: console.cloud.google.com → IAM & Admin → Service Accounts
SERVICE_ACCOUNT_FILE = '/path/to/service_account.json'

# Path to your OAuth2 client secret JSON file
# Create at: console.cloud.google.com → APIs & Services → Credentials
CLIENT_SECRET_FILE = '/path/to/client_secret.json'

# Optional: Dropbox access token for archiving
# Get at: dropbox.com/developers/apps
DROPBOX_ACCESS_TOKEN = None

# Optional: OpenAI API key for AI-powered classification
# Get at: platform.openai.com/api-keys
OPENAI_API_KEY = None

# Project patterns for email classification
# Maps domain/keyword to project name
PROJECT_PATTERNS = {
    'active_project': {
        # 'example.com': 'Example Project',
        # 'contractor@email.com': 'Renovation',
    },
    'archive_project': {
        # 'old-client.com': 'Old Client Project',
    },
    'soft_delete': [
        # Domains to auto-delete
        # 'marketing-spam.com',
    ],
    'always_keep': [
        # Important domains to never delete
        # 'bank.com',
        # 'employer.com',
    ]
}

# Marketing/notification patterns (will be soft-deleted)
MARKETING_PATTERNS = [
    'unsubscribe',
    'opt-out',
    'email preferences',
    'marketing',
    'newsletter',
    'promotional',
]

# Notification senders (will be labeled, not deleted)
NOTIFICATION_SENDERS = [
    # 'noreply@example.com',
    # 'notifications@service.com',
]
