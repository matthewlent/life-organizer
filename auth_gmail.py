#!/usr/bin/env python3
"""
Gmail OAuth2 authentication script.
Run once to get refresh token, then API access works indefinitely.
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Import configuration
try:
    from config import CLIENT_SECRET_FILE
except ImportError:
    raise ImportError(
        "config.py not found. Copy config.example.py to config.py and fill in your values."
    )

# Gmail, Calendar, and Contacts API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.labels',
    'https://www.googleapis.com/auth/gmail.settings.basic',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/contacts',
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(SCRIPT_DIR, 'gmail_token.json')


def authenticate():
    """Run OAuth flow and save credentials."""
    creds = None

    # Check for existing token
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If no valid credentials, run OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRET_FILE):
                raise FileNotFoundError(
                    f"Client secret file not found: {CLIENT_SECRET_FILE}\n"
                    "Please update CLIENT_SECRET_FILE in config.py"
                )
            print("Starting OAuth flow...")
            print("A browser window will open. Log in and click 'Allow'.")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)

        # Save credentials
        with open(TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
        print(f"Token saved to {TOKEN_FILE}")

    return creds


def main():
    creds = authenticate()

    if creds and creds.valid:
        print("\nGmail authentication successful!")
        print(f"  Token file: {TOKEN_FILE}")
        print(f"  Scopes: {', '.join(SCOPES)}")
    else:
        print("\nAuthentication failed")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
