#!/usr/bin/env python3
"""
Tests for iMessage parser.
"""

import pytest
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAppleTimestamp:
    """Test Apple timestamp conversion."""

    def test_nanosecond_timestamp(self):
        """Test conversion of nanosecond timestamps."""
        from imessage_parser import convert_apple_timestamp

        # A timestamp in nanoseconds (after 2020)
        # 2020-01-01 00:00:00 in Apple epoch
        apple_epoch = datetime(2001, 1, 1)
        test_date = datetime(2020, 1, 1)
        seconds_diff = (test_date - apple_epoch).total_seconds()
        ns_timestamp = int(seconds_diff * 1e9)

        result = convert_apple_timestamp(ns_timestamp)

        # Should be close to 2020-01-01
        assert result.year == 2020
        assert result.month == 1
        assert result.day == 1

    def test_seconds_timestamp(self):
        """Test conversion of seconds timestamps."""
        from imessage_parser import convert_apple_timestamp

        # A timestamp in seconds
        apple_epoch = datetime(2001, 1, 1)
        test_date = datetime(2020, 6, 15)
        seconds_diff = (test_date - apple_epoch).total_seconds()

        result = convert_apple_timestamp(int(seconds_diff))

        assert result.year == 2020
        assert result.month == 6
        assert result.day == 15


class TestConversation:
    """Test conversation data structures."""

    def test_conversation_dataclass(self):
        """Test Conversation dataclass creation."""
        from imessage_parser import Conversation

        conv = Conversation(
            handle='+15551234567',
            display_name='John Doe',
            message_count=10,
            last_message_date=datetime.now(),
            last_message_from_me=False,
            needs_response=True
        )

        assert conv.handle == '+15551234567'
        assert conv.display_name == 'John Doe'
        assert conv.message_count == 10
        assert conv.needs_response is True


class TestMessage:
    """Test message data structures."""

    def test_message_to_dict(self):
        """Test Message to_dict method."""
        from imessage_parser import Message

        msg = Message(
            rowid=123,
            date=datetime(2024, 1, 15, 10, 30),
            text='Hello there! How are you doing today?',
            is_from_me=False,
            handle='+15551234567',
            display_name='Jane'
        )

        result = msg.to_dict()

        assert result['rowid'] == 123
        assert result['text'] == 'Hello there! How are you doing today?'
        assert result['is_from_me'] is False
        assert result['handle'] == '+15551234567'
        assert result['display_name'] == 'Jane'

    def test_long_text_truncated(self):
        """Test that long text is truncated in to_dict."""
        from imessage_parser import Message

        long_text = 'A' * 500

        msg = Message(
            rowid=1,
            date=datetime.now(),
            text=long_text,
            is_from_me=True,
            handle='test'
        )

        result = msg.to_dict()

        assert len(result['text']) == 200
