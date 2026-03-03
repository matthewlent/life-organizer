#!/usr/bin/env python3
"""
Email classification system.

Uses rule-based patterns first (fast), then falls back to AI if available.
"""

import re
from typing import Dict, Any, List, Optional

# Import configuration
try:
    from config import (
        PROJECT_PATTERNS,
        MARKETING_PATTERNS,
        NOTIFICATION_SENDERS,
        OPENAI_API_KEY
    )
except ImportError:
    PROJECT_PATTERNS = {'active_project': {}, 'archive_project': {}, 'soft_delete': [], 'always_keep': []}
    MARKETING_PATTERNS = ['unsubscribe', 'opt-out', 'email preferences']
    NOTIFICATION_SENDERS = []
    OPENAI_API_KEY = None


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


def quick_classify(email_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Quick rule-based classification for obvious cases.
    Returns None if no clear match.
    """
    subject = email_data.get('subject', '').lower()
    from_addr = email_data.get('from', '').lower()
    body = email_data.get('body', '').lower()
    domain = extract_domain(from_addr)
    email_addr = extract_email_address(from_addr)

    combined_text = f"{subject} {body[:1000]}"

    # Check always_keep first
    for pattern in PROJECT_PATTERNS.get('always_keep', []):
        if pattern.lower() in domain or pattern.lower() in email_addr:
            return {
                'category': 'needs_review',
                'project': '',
                'is_key_email': True,
                'confidence': 0.9,
                'reason': f'Important sender: {pattern}'
            }

    # Check soft_delete patterns
    for pattern in PROJECT_PATTERNS.get('soft_delete', []):
        if pattern.lower() in domain:
            return {
                'category': 'soft_delete',
                'project': '',
                'is_key_email': False,
                'confidence': 0.9,
                'reason': f'Soft delete pattern: {pattern}'
            }

    # Check active project patterns
    for pattern, project in PROJECT_PATTERNS.get('active_project', {}).items():
        if pattern.lower() in domain or pattern.lower() in email_addr or pattern.lower() in combined_text:
            return {
                'category': 'active_project',
                'project': project,
                'is_key_email': True,
                'confidence': 0.95,
                'reason': f'Active project match: {pattern}'
            }

    # Check archive project patterns
    for pattern, project in PROJECT_PATTERNS.get('archive_project', {}).items():
        if pattern.lower() in domain or pattern.lower() in email_addr or pattern.lower() in combined_text:
            return {
                'category': 'archive_project',
                'project': project,
                'is_key_email': False,
                'confidence': 0.9,
                'reason': f'Archive project match: {pattern}'
            }

    # Check marketing patterns
    for pattern in MARKETING_PATTERNS:
        if pattern.lower() in combined_text:
            return {
                'category': 'soft_delete',
                'project': '',
                'is_key_email': False,
                'confidence': 0.8,
                'reason': f'Marketing pattern: {pattern}'
            }

    # Check notification senders
    for sender in NOTIFICATION_SENDERS:
        if sender.lower() in email_addr:
            return {
                'category': 'soft_delete',
                'project': '',
                'is_key_email': False,
                'confidence': 0.85,
                'reason': f'Notification sender: {sender}'
            }

    return None


def classify_with_ai(email_data: Dict[str, Any], projects: List[Dict]) -> Optional[Dict[str, Any]]:
    """
    Use AI (OpenAI) to classify email.
    Returns None if AI not available or fails.
    """
    if not OPENAI_API_KEY:
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)

        project_list = ', '.join([p.get('Name', '') for p in projects if p.get('Name')])

        prompt = f"""Classify this email into one of these categories:
- active_project: Related to an active project ({project_list or 'no projects defined'})
- archive_project: Related to a finished/old project
- personal: Personal correspondence
- soft_delete: Marketing, newsletters, notifications
- needs_review: Unclear, needs human review

Email:
From: {email_data.get('from', '')}
Subject: {email_data.get('subject', '')}
Body: {email_data.get('body', '')[:500]}

Respond with JSON:
{{"category": "...", "project": "...", "is_key_email": true/false, "confidence": 0.0-1.0, "reason": "..."}}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=200
        )

        import json
        result = json.loads(response.choices[0].message.content)
        result['reason'] = f"[AI] {result.get('reason', '')}"
        return result

    except Exception as e:
        print(f"AI classification failed: {e}")
        return None


def fallback_classify(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback classification when rules and AI don't match.
    Conservative - marks for review.
    """
    subject = email_data.get('subject', '').lower()
    from_addr = email_data.get('from', '').lower()

    # Check for common personal indicators
    personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'icloud.com']
    domain = extract_domain(from_addr)

    if domain in personal_domains:
        return {
            'category': 'personal',
            'project': '',
            'is_key_email': False,
            'confidence': 0.5,
            'reason': '[Fallback] Personal email domain'
        }

    # Default to needs_review
    return {
        'category': 'needs_review',
        'project': '',
        'is_key_email': False,
        'confidence': 0.3,
        'reason': '[Fallback] No clear classification'
    }


def classify_email(email_data: Dict[str, Any], projects: List[Dict] = None,
                   headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Main classification function.

    Tries in order:
    1. Quick rule-based classification
    2. AI classification (if available)
    3. Fallback rules

    Returns dict with:
    - category: Classification category
    - project: Project name (if applicable)
    - is_key_email: Whether this is important
    - confidence: 0.0-1.0 confidence score
    - reason: Explanation
    """
    projects = projects or []

    # Try quick rules first
    result = quick_classify(email_data)
    if result:
        return result

    # Try AI classification
    result = classify_with_ai(email_data, projects)
    if result:
        return result

    # Fall back to simple rules
    return fallback_classify(email_data)
