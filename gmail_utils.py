#!/usr/bin/env python3
"""
Gmail API utilities for email processing.
"""

import os
import base64
import email
import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(SCRIPT_DIR, 'gmail_token.json')

# Label prefix for organization
LABEL_PREFIX = 'organized'

# Cache for service and labels
_service = None
_labels_cache = None


def get_service():
    """Get authenticated Gmail service (cached)."""
    global _service
    if _service is None:
        if not os.path.exists(TOKEN_FILE):
            raise FileNotFoundError(
                f"Token file not found: {TOKEN_FILE}\n"
                "Run auth_gmail.py first to authenticate."
            )
        creds = Credentials.from_authorized_user_file(TOKEN_FILE)
        _service = build('gmail', 'v1', credentials=creds)
    return _service


def get_labels() -> Dict[str, str]:
    """Get all labels as name -> id mapping (cached)."""
    global _labels_cache
    if _labels_cache is None:
        service = get_service()
        results = service.users().labels().list(userId='me').execute()
        _labels_cache = {label['name']: label['id'] for label in results.get('labels', [])}
    return _labels_cache


def create_label(name: str) -> str:
    """Create a label if it doesn't exist, return label ID."""
    global _labels_cache
    labels = get_labels()

    if name in labels:
        return labels[name]

    service = get_service()
    label_body = {
        'name': name,
        'labelListVisibility': 'labelShow',
        'messageListVisibility': 'show'
    }

    result = service.users().labels().create(userId='me', body=label_body).execute()
    label_id = result['id']

    # Update cache
    _labels_cache[name] = label_id
    return label_id


def ensure_label(category: str, project: str = None) -> str:
    """
    Ensure organizational label exists and return its ID.
    Format: organized/{category}/{project} or organized/{category}
    """
    if project:
        # Sanitize project name for label
        project_label = re.sub(r'[^\w\s-]', '', project).strip().lower().replace(' ', '-')
        label_name = f"{LABEL_PREFIX}/{category}/{project_label}"
    else:
        label_name = f"{LABEL_PREFIX}/{category}"

    return create_label(label_name)


def get_message(message_id: str, format: str = 'full') -> Dict[str, Any]:
    """Get a single message by ID."""
    service = get_service()
    return service.users().messages().get(
        userId='me',
        id=message_id,
        format=format
    ).execute()


def get_message_raw(message_id: str) -> bytes:
    """Get raw message content for saving as .eml file."""
    service = get_service()
    message = service.users().messages().get(
        userId='me',
        id=message_id,
        format='raw'
    ).execute()
    return base64.urlsafe_b64decode(message['raw'])


def parse_headers(headers: List[Dict]) -> Dict[str, str]:
    """Parse headers list into dict."""
    return {h['name'].lower(): h['value'] for h in headers}


def extract_email_address(sender: str) -> str:
    """Extract email address from sender string."""
    match = re.search(r'<([^>]+)>', sender)
    if match:
        return match.group(1).lower()
    return sender.lower().strip()


def extract_domain(email_addr: str) -> str:
    """Extract domain from email address."""
    match = re.search(r'@([^>\s]+)', email_addr)
    return match.group(1) if match else 'unknown'


def get_body(payload: Dict) -> str:
    """Extract plain text body from email payload."""
    body = ""

    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    break
            elif 'parts' in part:
                body = get_body(part)
                if body:
                    break
    else:
        data = payload['body'].get('data', '')
        if data:
            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')

    return body


def get_attachments(message: Dict) -> List[Dict[str, Any]]:
    """Extract attachment info from message."""
    attachments = []

    def process_parts(parts):
        for part in parts:
            filename = part.get('filename', '')
            if filename:
                attachments.append({
                    'filename': filename,
                    'mime_type': part.get('mimeType', 'application/octet-stream'),
                    'size': int(part['body'].get('size', 0)),
                    'attachment_id': part['body'].get('attachmentId')
                })
            if 'parts' in part:
                process_parts(part['parts'])

    if 'parts' in message['payload']:
        process_parts(message['payload']['parts'])

    return attachments


def download_attachment(message_id: str, attachment_id: str) -> bytes:
    """Download attachment content."""
    service = get_service()
    attachment = service.users().messages().attachments().get(
        userId='me',
        messageId=message_id,
        id=attachment_id
    ).execute()
    return base64.urlsafe_b64decode(attachment['data'])


def apply_labels(message_id: str, add_labels: List[str] = None, remove_labels: List[str] = None):
    """Apply labels to a message."""
    service = get_service()

    body = {}
    if add_labels:
        body['addLabelIds'] = add_labels
    if remove_labels:
        body['removeLabelIds'] = remove_labels

    if body:
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body=body
        ).execute()


def label_message(message_id: str, category: str, project: str = None):
    """Label a message with organizational category."""
    label_id = ensure_label(category, project)
    apply_labels(message_id, add_labels=[label_id])


def trash_message(message_id: str):
    """Move message to trash."""
    service = get_service()
    service.users().messages().trash(userId='me', id=message_id).execute()


def archive_message(message_id: str):
    """Archive message (remove from inbox)."""
    apply_labels(message_id, remove_labels=['INBOX'])


def list_messages(query: str = None, max_results: int = 100,
                  page_token: str = None) -> Dict[str, Any]:
    """
    List messages matching query.
    Returns dict with 'messages' list and 'nextPageToken'.
    """
    service = get_service()

    params = {
        'userId': 'me',
        'maxResults': max_results
    }
    if query:
        params['q'] = query
    if page_token:
        params['pageToken'] = page_token

    return service.users().messages().list(**params).execute()


def get_email_date(message: Dict) -> Optional[datetime]:
    """Parse email date from message."""
    headers = parse_headers(message['payload']['headers'])
    date_str = headers.get('date', '')

    if not date_str:
        return None

    # Try parsing common date formats
    formats = [
        '%a, %d %b %Y %H:%M:%S %z',
        '%a, %d %b %Y %H:%M:%S %Z',
        '%d %b %Y %H:%M:%S %z',
        '%a, %d %b %Y %H:%M:%S',
    ]

    # Remove timezone abbreviations like (PST)
    date_str = re.sub(r'\s*\([A-Z]{3,4}\)\s*$', '', date_str)

    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue

    return None


def format_email_summary(message: Dict) -> Dict[str, Any]:
    """Format message into summary dict."""
    headers = parse_headers(message['payload']['headers'])

    return {
        'id': message['id'],
        'thread_id': message['threadId'],
        'subject': headers.get('subject', '(no subject)'),
        'from': headers.get('from', 'Unknown'),
        'to': headers.get('to', ''),
        'date': headers.get('date', ''),
        'snippet': message.get('snippet', ''),
        'labels': message.get('labelIds', []),
        'attachments': get_attachments(message)
    }
