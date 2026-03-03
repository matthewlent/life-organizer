#!/usr/bin/env python3
"""
Google Sheets utilities for logging and data management.
"""

import os
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials
from typing import List, Dict, Any, Optional

# Import configuration
try:
    from config import SERVICE_ACCOUNT_FILE, SHEET_ID
except ImportError:
    raise ImportError(
        "config.py not found. Copy config.example.py to config.py and fill in your values."
    )

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Cache
_client = None
_spreadsheet = None


def get_client():
    """Get authenticated gspread client (cached)."""
    global _client
    if _client is None:
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            raise FileNotFoundError(
                f"Service account file not found: {SERVICE_ACCOUNT_FILE}\n"
                "Please update SERVICE_ACCOUNT_FILE in config.py"
            )
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        _client = gspread.authorize(creds)
    return _client


def get_spreadsheet():
    """Get spreadsheet object (cached)."""
    global _spreadsheet
    if _spreadsheet is None:
        client = get_client()
        _spreadsheet = client.open_by_key(SHEET_ID)
    return _spreadsheet


def ensure_tab(name: str, headers: List[str] = None) -> gspread.Worksheet:
    """Ensure a tab exists, create if needed with headers."""
    spreadsheet = get_spreadsheet()
    existing_tabs = [ws.title for ws in spreadsheet.worksheets()]

    if name not in existing_tabs:
        ws = spreadsheet.add_worksheet(title=name, rows=1000, cols=20)
        if headers:
            ws.append_row(headers)
            ws.format(f'A1:{chr(64 + len(headers))}1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
            })
    else:
        ws = spreadsheet.worksheet(name)

    return ws


def get_projects() -> List[Dict[str, Any]]:
    """Get all projects from Projects tab."""
    spreadsheet = get_spreadsheet()
    ws = spreadsheet.worksheet('Projects')
    records = ws.get_all_records()
    return records


def get_relationships() -> List[Dict[str, Any]]:
    """Get all relationships from Relationships tab."""
    spreadsheet = get_spreadsheet()
    ws = spreadsheet.worksheet('Relationships')
    records = ws.get_all_records()
    return records


def log_processing(email_id: str, subject: str, from_addr: str,
                   action: str, destination: str = '', project: str = '', notes: str = ''):
    """Log an email processing action."""
    ws = ensure_tab('Processing Log', [
        'Timestamp', 'Email ID', 'Subject', 'From', 'Action', 'Destination', 'Project', 'Notes'
    ])

    ws.append_row([
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        email_id,
        subject[:100],
        from_addr[:50],
        action,
        destination,
        project,
        notes
    ])


def add_question(question_type: str, question: str, context: str,
                 email_id: str = '', options: str = ''):
    """Add item to Questions tab for human review."""
    ws = ensure_tab('Questions', [
        'Date', 'Type', 'Question', 'Context', 'Email ID', 'Options', 'Answer', 'Resolved'
    ])

    ws.append_row([
        datetime.now().strftime('%Y-%m-%d'),
        question_type,
        question,
        context[:500],
        email_id,
        options,
        '',  # Answer - to be filled by user
        ''   # Resolved - to be filled by user
    ])


def add_todo(task: str, task_type: str, source: str,
             person: str = '', project: str = '', priority: str = 'Medium',
             due: str = '', notes: str = ''):
    """Add item to To-Do tab."""
    ws = ensure_tab('To-Do', [
        'Task', 'Type', 'Source', 'Person', 'Project', 'Priority', 'Due', 'Done', 'Added', 'Notes'
    ])

    ws.append_row([
        task,
        task_type,
        source,
        person,
        project,
        priority,
        due,
        '',  # Done checkbox
        datetime.now().strftime('%Y-%m-%d'),
        notes
    ])


def update_relationship(email: str, last_contact: str = None, notes: str = None):
    """Update last contact date for a relationship."""
    spreadsheet = get_spreadsheet()
    ws = spreadsheet.worksheet('Relationships')
    records = ws.get_all_records()

    for i, row in enumerate(records):
        if row['Email'].lower() == email.lower():
            row_num = i + 2  # +2 for header and 0-index

            if last_contact:
                ws.update_cell(row_num, 5, last_contact)  # Last Contact column

            if notes:
                current_notes = row.get('Notes', '')
                if current_notes:
                    new_notes = f"{current_notes}; {notes}"
                else:
                    new_notes = notes
                ws.update_cell(row_num, 7, new_notes)  # Notes column

            return True

    return False


def add_relationship(name: str, email: str, relationship: str, context: str,
                     last_contact: str = None):
    """Add new relationship if doesn't exist."""
    spreadsheet = get_spreadsheet()
    ws = spreadsheet.worksheet('Relationships')
    records = ws.get_all_records()

    # Check if exists
    for row in records:
        if row['Email'].lower() == email.lower():
            return False  # Already exists

    ws.append_row([
        name,
        email,
        relationship,
        context,
        last_contact or datetime.now().strftime('%b %d, %Y'),
        '',  # Follow Up
        ''   # Notes
    ])
    return True


def log_dry_run(rows: List[Dict[str, Any]]):
    """Log dry run results to a special tab."""
    ws = ensure_tab('Dry Run', [
        'Email ID', 'Subject', 'From', 'Date',
        'Category', 'Project', 'Key Email?', 'Confidence',
        'Action', 'Destination', 'Reason'
    ])

    # Clear previous dry run data (except header)
    if ws.row_count > 1:
        ws.delete_rows(2, ws.row_count)

    # Add new data
    for row in rows:
        ws.append_row([
            row.get('email_id', ''),
            row.get('subject', '')[:80],
            row.get('from', '')[:50],
            row.get('date', ''),
            row.get('category', ''),
            row.get('project', ''),
            'Yes' if row.get('is_key_email') else 'No',
            f"{row.get('confidence', 0):.0%}",
            row.get('action', ''),
            row.get('destination', ''),
            row.get('reason', '')[:200]
        ])

    return ws
