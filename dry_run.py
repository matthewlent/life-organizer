#!/usr/bin/env python3
"""
Dry run script - classify sample emails and show what would happen.
Results logged to 'Dry Run' tab in Google Sheets for review.
"""

import os
import sys
from datetime import datetime, timedelta

import gmail_utils
import sheets_utils
from classify import classify_email

# Action descriptions for each category
ACTIONS = {
    'active_project': 'Label in Gmail (organized/active/{project})',
    'archive_project': 'Archive to Dropbox, remove from Gmail',
    'personal': 'Label in Gmail (organized/personal), update Relationships',
    'soft_delete': 'Add to monthly soft-delete zip',
    'needs_review': 'Add to Questions tab for manual review'
}

# Destination descriptions
DESTINATIONS = {
    'active_project': 'Gmail + Dropbox (if key email)',
    'archive_project': '/Projects/{project}/Email/',
    'personal': 'Gmail only',
    'soft_delete': '/Archive/Email-Deleted/{YYYY-MM}.zip',
    'needs_review': 'Pending review'
}


def run_dry_run(num_emails: int = 20, days: int = 30):
    """
    Run classification on sample emails without making changes.

    Args:
        num_emails: Number of emails to sample
        days: Look back this many days
    """
    print("=" * 60)
    print("LIFE ORGANIZER - DRY RUN")
    print("=" * 60)
    print(f"\nSampling {num_emails} emails from last {days} days...")
    print("No changes will be made - just showing what WOULD happen.\n")

    # Get projects from spreadsheet
    print("Loading projects from spreadsheet...")
    try:
        projects = sheets_utils.get_projects()
        print(f"  Found {len(projects)} projects")
    except Exception as e:
        print(f"  Warning: Could not load projects: {e}")
        projects = []

    # Build query
    after_date = (datetime.now() - timedelta(days=days)).strftime('%Y/%m/%d')
    query = f'after:{after_date}'

    # Fetch emails
    print(f"\nFetching emails...")
    result = gmail_utils.list_messages(query=query, max_results=num_emails)
    messages = result.get('messages', [])
    print(f"  Found {len(messages)} emails")

    if not messages:
        print("No emails found!")
        return

    # Process each email
    dry_run_results = []
    print(f"\nClassifying emails...\n")
    print("-" * 60)

    for i, msg in enumerate(messages):
        try:
            # Get full message
            full_msg = gmail_utils.get_message(msg['id'])
            headers = gmail_utils.parse_headers(full_msg['payload']['headers'])

            subject = headers.get('subject', '(no subject)')
            from_addr = headers.get('from', 'Unknown')
            date = headers.get('date', '')

            print(f"[{i+1}/{len(messages)}] {subject[:60]}")
            print(f"         From: {from_addr[:50]}")

            # Build email data for classification
            email_data = {
                'id': msg['id'],
                'subject': subject,
                'from': from_addr,
                'to': headers.get('to', ''),
                'date': date,
                'body': gmail_utils.get_body(full_msg['payload']),
                'snippet': full_msg.get('snippet', ''),
                'attachments': gmail_utils.get_attachments(full_msg)
            }

            # Classify (uses quick rules first, then AI if available, then fallback rules)
            classification = classify_email(email_data, projects, headers)

            # Show classification type
            reason = classification.get('reason', '')
            if reason.startswith('[AI]'):
                method = 'AI'
            elif reason.startswith('[Fallback]'):
                method = 'RULES'
            elif 'Marketing' in reason or 'notification' in reason.lower():
                method = 'QUICK'
            else:
                method = 'RULES'

            print(f"         [{method}] -> {classification['category']} ({classification['confidence']:.0%})")

            # Determine action and destination
            category = classification['category']
            project = classification.get('project', '')
            action = ACTIONS.get(category, 'Unknown')
            destination = DESTINATIONS.get(category, '')

            if category == 'active_project' and project:
                action = action.format(project=project)
                if classification.get('is_key_email'):
                    destination = f"/Projects/{project}/Email/"
            elif category == 'archive_project' and project:
                destination = destination.format(project=project)

            # Store result
            dry_run_results.append({
                'email_id': msg['id'],
                'subject': subject,
                'from': from_addr,
                'date': date,
                'category': category,
                'project': project or '',
                'is_key_email': classification.get('is_key_email', False),
                'confidence': classification.get('confidence', 0),
                'action': action,
                'destination': destination,
                'reason': classification.get('reason', '')
            })

            if classification.get('reason'):
                print(f"         Reason: {classification['reason'][:60]}")
            print()

        except Exception as e:
            print(f"         ERROR: {e}")
            dry_run_results.append({
                'email_id': msg['id'],
                'subject': f"Error: {str(e)[:50]}",
                'from': '',
                'date': '',
                'category': 'error',
                'project': '',
                'is_key_email': False,
                'confidence': 0,
                'action': 'Skip - error occurred',
                'destination': '',
                'reason': str(e)
            })
            print()

    # Summary
    print("-" * 60)
    print("\nSUMMARY:")
    print("-" * 60)

    by_category = {}
    for r in dry_run_results:
        cat = r['category']
        by_category[cat] = by_category.get(cat, 0) + 1

    for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")

    # Log to spreadsheet
    print("\nLogging results to Google Sheets 'Dry Run' tab...")
    try:
        from config import SHEET_ID
        ws = sheets_utils.log_dry_run(dry_run_results)
        print(f"  Done! View at: https://docs.google.com/spreadsheets/d/{SHEET_ID}")
    except Exception as e:
        print(f"  Error logging to sheets: {e}")

    print("\n" + "=" * 60)
    print("DRY RUN COMPLETE")
    print("Review the 'Dry Run' tab in your spreadsheet.")
    print("No changes were made to Gmail or Dropbox.")
    print("=" * 60)


def main():
    # Parse arguments
    num_emails = 20
    days = 30

    if len(sys.argv) > 1:
        try:
            num_emails = int(sys.argv[1])
        except ValueError:
            pass

    if len(sys.argv) > 2:
        try:
            days = int(sys.argv[2])
        except ValueError:
            pass

    run_dry_run(num_emails=num_emails, days=days)


if __name__ == '__main__':
    main()
