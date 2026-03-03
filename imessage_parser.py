#!/usr/bin/env python3
"""
iMessage database parser for relationship tracking.

REQUIRES: Full Disk Access for Terminal
Enable at: System Settings -> Privacy & Security -> Full Disk Access -> Add Terminal

Usage:
    python imessage_parser.py [--days N] [--dry-run]
"""

import os
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# iMessage database location
IMESSAGE_DB = os.path.expanduser('~/Library/Messages/chat.db')


@dataclass
class Message:
    """Represents a single iMessage."""
    rowid: int
    date: datetime
    text: str
    is_from_me: bool
    handle: str  # Phone number or email
    display_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'rowid': self.rowid,
            'date': self.date.isoformat(),
            'text': self.text[:200] if self.text else '',
            'is_from_me': self.is_from_me,
            'handle': self.handle,
            'display_name': self.display_name,
        }


@dataclass
class Conversation:
    """Represents a conversation with a contact."""
    handle: str
    display_name: Optional[str]
    message_count: int
    last_message_date: datetime
    last_message_from_me: bool
    needs_response: bool = False
    messages: List[Message] = None


def check_access() -> bool:
    """Check if we have access to the iMessage database."""
    if not os.path.exists(IMESSAGE_DB):
        print(f"iMessage database not found at {IMESSAGE_DB}")
        return False

    try:
        conn = sqlite3.connect(IMESSAGE_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM message")
        count = cursor.fetchone()[0]
        conn.close()
        print(f"Access granted. Found {count} messages.")
        return True
    except sqlite3.OperationalError as e:
        if 'unable to open database file' in str(e):
            print("=" * 60)
            print("ACCESS DENIED: Full Disk Access required")
            print("=" * 60)
            print("\nTo enable:")
            print("1. Open System Settings")
            print("2. Go to Privacy & Security -> Full Disk Access")
            print("3. Click + and add Terminal (or your terminal app)")
            print("4. Restart Terminal")
            print("\nThen try again.")
            return False
        raise


def convert_apple_timestamp(apple_timestamp: int) -> datetime:
    """Convert Apple's timestamp to datetime."""
    # Apple uses nanoseconds since 2001-01-01
    # We need to convert to seconds and add the epoch difference
    if apple_timestamp > 1e15:
        # Nanoseconds
        seconds = apple_timestamp / 1e9
    else:
        # Already in seconds
        seconds = apple_timestamp

    # Apple epoch is 2001-01-01 00:00:00
    apple_epoch = datetime(2001, 1, 1)
    return apple_epoch + timedelta(seconds=seconds)


class IMessageParser:
    """Parser for iMessage database."""

    def __init__(self):
        self.conn = None
        self.messages: List[Message] = []
        self.conversations: Dict[str, Conversation] = {}

    def connect(self) -> bool:
        """Connect to the iMessage database."""
        if not check_access():
            return False

        self.conn = sqlite3.connect(IMESSAGE_DB)
        self.conn.row_factory = sqlite3.Row
        return True

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def get_messages(self, days: int = 30, limit: int = 1000) -> List[Message]:
        """
        Fetch recent messages.

        Args:
            days: Look back this many days
            limit: Maximum messages to fetch

        Returns:
            List of Message objects
        """
        if not self.conn:
            if not self.connect():
                return []

        cursor = self.conn.cursor()

        # Calculate timestamp cutoff
        cutoff = datetime.now() - timedelta(days=days)
        apple_epoch = datetime(2001, 1, 1)
        cutoff_timestamp = (cutoff - apple_epoch).total_seconds() * 1e9

        query = """
        SELECT
            m.ROWID,
            m.date,
            m.text,
            m.is_from_me,
            h.id as handle,
            COALESCE(c.display_name, h.id) as display_name
        FROM message m
        LEFT JOIN handle h ON m.handle_id = h.ROWID
        LEFT JOIN chat_message_join cmj ON m.ROWID = cmj.message_id
        LEFT JOIN chat c ON cmj.chat_id = c.ROWID
        WHERE m.date > ?
        ORDER BY m.date DESC
        LIMIT ?
        """

        cursor.execute(query, (cutoff_timestamp, limit))

        messages = []
        for row in cursor.fetchall():
            if row['text']:  # Skip empty messages
                msg = Message(
                    rowid=row['ROWID'],
                    date=convert_apple_timestamp(row['date']),
                    text=row['text'],
                    is_from_me=bool(row['is_from_me']),
                    handle=row['handle'] or 'Unknown',
                    display_name=row['display_name']
                )
                messages.append(msg)

        self.messages = messages
        return messages

    def get_conversations(self, days: int = 30) -> Dict[str, Conversation]:
        """
        Get conversation summaries.

        Args:
            days: Look back this many days

        Returns:
            Dict of handle -> Conversation
        """
        messages = self.get_messages(days=days)

        conversations: Dict[str, Conversation] = {}

        for msg in messages:
            handle = msg.handle

            if handle not in conversations:
                conversations[handle] = Conversation(
                    handle=handle,
                    display_name=msg.display_name,
                    message_count=0,
                    last_message_date=msg.date,
                    last_message_from_me=msg.is_from_me,
                    messages=[]
                )

            conv = conversations[handle]
            conv.message_count += 1

            if msg.date > conv.last_message_date:
                conv.last_message_date = msg.date
                conv.last_message_from_me = msg.is_from_me

            if conv.messages is not None:
                conv.messages.append(msg)

        # Determine which conversations need a response
        for handle, conv in conversations.items():
            if not conv.last_message_from_me:
                # Last message was from them, might need response
                time_since = datetime.now() - conv.last_message_date
                if time_since > timedelta(hours=24):
                    conv.needs_response = True

        self.conversations = conversations
        return conversations

    def get_contacts_needing_response(self) -> List[Conversation]:
        """Get conversations where we haven't responded."""
        if not self.conversations:
            self.get_conversations()

        return [
            conv for conv in self.conversations.values()
            if conv.needs_response
        ]

    def get_last_contact_dates(self) -> Dict[str, datetime]:
        """Get last contact date for each handle."""
        if not self.conversations:
            self.get_conversations()

        return {
            handle: conv.last_message_date
            for handle, conv in self.conversations.items()
        }


def find_action_items(parser: IMessageParser, days: int = 30) -> List[Message]:
    """
    Find messages that might contain action items.

    Looks for keywords like payment, invoice, reminder, etc.
    """
    messages = parser.get_messages(days=days)

    keywords = [
        'payment', 'pay', 'paid', 'invoice', 'receipt',
        'reminder', 'don\'t forget', 'remember to',
        'meeting', 'appointment', 'schedule',
        'deadline', 'due', 'by tomorrow', 'by friday',
        'call me', 'text me', 'let me know',
        'confirm', 'rsvp', 'reply',
        'venmo', 'zelle', 'cash', 'check',
    ]

    action_msgs = []
    for msg in messages:
        if not msg.text:
            continue
        text_lower = msg.text.lower()
        if any(kw in text_lower for kw in keywords):
            action_msgs.append(msg)

    return action_msgs


def main():
    import sys

    days = 30
    dry_run = True

    # Parse args
    for arg in sys.argv[1:]:
        if arg.startswith('--days='):
            days = int(arg.split('=')[1])
        elif arg == '--live':
            dry_run = False

    print("iMessage Parser")
    print("=" * 60)

    # Check access
    if not check_access():
        sys.exit(1)

    parser = IMessageParser()

    if not parser.connect():
        sys.exit(1)

    try:
        print(f"\nFetching messages from last {days} days...")
        messages = parser.get_messages(days=days)
        print(f"Found {len(messages)} messages")

        print("\nGetting conversations...")
        conversations = parser.get_conversations(days=days)
        print(f"Found {len(conversations)} conversations")

        # Needing response
        needs_response = parser.get_contacts_needing_response()
        print(f"\nConversations needing response: {len(needs_response)}")

        if needs_response:
            print("\n" + "-" * 40)
            print("NEEDS RESPONSE:")
            print("-" * 40)
            for conv in sorted(needs_response, key=lambda c: c.last_message_date, reverse=True)[:10]:
                age = datetime.now() - conv.last_message_date
                print(f"  {conv.display_name or conv.handle}")
                print(f"    Last message: {age.days}d {age.seconds//3600}h ago")
                if conv.messages:
                    last_msg = conv.messages[0]
                    print(f"    \"{last_msg.text[:60]}...\"" if len(last_msg.text) > 60 else f"    \"{last_msg.text}\"")
                print()

        # Action items
        print("\n" + "-" * 40)
        print("POTENTIAL ACTION ITEMS:")
        print("-" * 40)
        action_msgs = find_action_items(parser, days=days)
        print(f"Found {len(action_msgs)} potential action items")

        for msg in action_msgs[:5]:
            print(f"\n  From: {msg.display_name or msg.handle}")
            print(f"  Date: {msg.date.strftime('%Y-%m-%d')}")
            print(f"  Text: {msg.text[:100]}...")

    finally:
        parser.close()

    print("\n" + "=" * 60)
    if dry_run:
        print("DRY RUN - No changes made")
        print("Run with --live to update Relationships tab")


if __name__ == '__main__':
    main()
