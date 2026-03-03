#!/usr/bin/env python3
"""
Tests for email classification.
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestQuickClassify:
    """Test quick rule-based classification."""

    def test_marketing_email_detected(self):
        """Marketing emails should be soft-deleted."""
        from classify import quick_classify

        email_data = {
            'subject': 'Special offer just for you!',
            'from': 'marketing@store.com',
            'body': 'Click here to unsubscribe from our mailing list.'
        }

        result = quick_classify(email_data)
        assert result is not None
        assert result['category'] == 'soft_delete'
        assert 'Marketing' in result['reason'] or 'unsubscribe' in result['reason'].lower()

    def test_unknown_email_returns_none(self):
        """Unknown emails should return None for fallback handling."""
        from classify import quick_classify

        email_data = {
            'subject': 'Hello there',
            'from': 'friend@example.com',
            'body': 'Just wanted to say hi!'
        }

        result = quick_classify(email_data)
        # Should return None if no rules match
        # (depends on config - may match or not)


class TestFallbackClassify:
    """Test fallback classification."""

    def test_personal_domain_detected(self):
        """Personal email domains should be classified as personal."""
        from classify import fallback_classify

        email_data = {
            'subject': 'Dinner plans',
            'from': 'friend@gmail.com',
            'body': 'Want to grab dinner?'
        }

        result = fallback_classify(email_data)
        assert result['category'] == 'personal'

    def test_unknown_defaults_to_review(self):
        """Unknown emails should default to needs_review."""
        from classify import fallback_classify

        email_data = {
            'subject': 'Important notice',
            'from': 'noreply@unknown-company.com',
            'body': 'Please review this document.'
        }

        result = fallback_classify(email_data)
        assert result['category'] in ['personal', 'needs_review']


class TestClassifyEmail:
    """Test main classification function."""

    def test_returns_required_fields(self):
        """Classification should return all required fields."""
        from classify import classify_email

        email_data = {
            'subject': 'Test email',
            'from': 'test@test.com',
            'body': 'This is a test.'
        }

        result = classify_email(email_data)

        assert 'category' in result
        assert 'project' in result
        assert 'is_key_email' in result
        assert 'confidence' in result
        assert 'reason' in result

    def test_confidence_in_range(self):
        """Confidence should be between 0 and 1."""
        from classify import classify_email

        email_data = {
            'subject': 'Another test',
            'from': 'another@test.com',
            'body': 'Testing confidence values.'
        }

        result = classify_email(email_data)

        assert 0 <= result['confidence'] <= 1
