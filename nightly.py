#!/usr/bin/env python3
"""
Nightly processing job for Life Organizer.

Runs all processing tasks:
1. Email processing (classify, label, archive)
2. iMessage processing (relationship updates)
3. To-Do generation

Usage:
    python nightly.py [--dry-run] [--emails N] [--days D]

For launchd scheduling, see com.life-organizer.nightly.plist
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any

import db
import sheets_utils

# Configure logging
LOG_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(LOG_DIR, 'nightly.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_email_processing(dry_run: bool = True, max_emails: int = 100,
                         days: int = 7) -> Dict[str, Any]:
    """Run email classification and processing."""
    logger.info(f"Starting email processing (dry_run={dry_run}, max={max_emails}, days={days})")

    try:
        # Import here to avoid circular imports
        from dry_run import run_dry_run

        if dry_run:
            run_dry_run(num_emails=max_emails, days=days)
            return {'total': max_emails, 'mode': 'dry_run'}
        else:
            # TODO: Implement live processing
            logger.warning("Live email processing not yet implemented")
            return {'total': 0, 'mode': 'live', 'warning': 'Not implemented'}

    except Exception as e:
        logger.error(f"Email processing error: {e}")
        return {'error': str(e), 'total': 0}


def run_imessage_processing(dry_run: bool = True, days: int = 7) -> Dict[str, Any]:
    """Run iMessage processing for relationship updates."""
    logger.info(f"Starting iMessage processing (dry_run={dry_run}, days={days})")

    try:
        from imessage_parser import IMessageParser, check_access

        if not check_access():
            logger.warning("iMessage access not available - skipping")
            return {'skipped': True, 'reason': 'No Full Disk Access'}

        parser = IMessageParser()
        if not parser.connect():
            return {'skipped': True, 'reason': 'Could not connect'}

        try:
            conversations = parser.get_conversations(days=days)
            needs_response = parser.get_contacts_needing_response()
            last_contacts = parser.get_last_contact_dates()

            logger.info(f"Found {len(conversations)} conversations, {len(needs_response)} needing response")

            # Update relationships (only in live mode)
            if not dry_run:
                for handle, last_date in last_contacts.items():
                    sheets_utils.update_relationship(
                        email=handle,  # Handle might be phone or email
                        last_contact=last_date.strftime('%Y-%m-%d')
                    )

            # Add to-dos for messages needing response
            todos_added = 0
            for conv in needs_response:
                if not dry_run:
                    sheets_utils.add_todo(
                        task=f"Respond to {conv.display_name or conv.handle}",
                        task_type='Response',
                        source='iMessage',
                        person=conv.display_name or conv.handle,
                        priority='Medium',
                        notes=f"Last message: {conv.last_message_date.strftime('%Y-%m-%d')}"
                    )
                todos_added += 1

            return {
                'conversations': len(conversations),
                'needs_response': len(needs_response),
                'todos_added': todos_added,
            }

        finally:
            parser.close()

    except ImportError:
        logger.warning("iMessage parser not available")
        return {'skipped': True, 'reason': 'Import error'}
    except Exception as e:
        logger.error(f"iMessage processing error: {e}")
        return {'error': str(e)}


def generate_relationship_todos(dry_run: bool = True) -> Dict[str, Any]:
    """Generate follow-up reminders based on relationship intervals."""
    logger.info("Generating relationship follow-up todos")

    try:
        relationships = sheets_utils.get_relationships()
        todos_added = 0

        for rel in relationships:
            follow_up = rel.get('Follow Up', '')
            last_contact = rel.get('Last Contact', '')
            name = rel.get('Name', '')

            if not follow_up or not last_contact:
                continue

            # Parse dates and intervals
            # This is a simplified version - could be enhanced
            # to parse various date/interval formats

            if not dry_run:
                # Check if follow-up is needed based on interval
                # For now, just log
                logger.debug(f"Would check follow-up for {name}")

        return {'checked': len(relationships), 'todos_added': todos_added}

    except Exception as e:
        logger.error(f"Relationship todo generation error: {e}")
        return {'error': str(e)}


def log_run_to_sheet(results: Dict[str, Any], dry_run: bool = True):
    """Log the nightly run results to the Processing Log."""
    if dry_run:
        return

    try:
        sheets_utils.log_processing(
            email_id='NIGHTLY_RUN',
            subject=f"Nightly run - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            from_addr='system',
            action='nightly_complete',
            destination='',
            project='',
            notes=f"Emails: {results.get('email', {}).get('total', 0)}, "
                  f"iMessage: {results.get('imessage', {}).get('conversations', 0)}"
        )
    except Exception as e:
        logger.error(f"Failed to log run to sheet: {e}")


def main():
    """Run the nightly processing job."""
    # Parse arguments
    dry_run = True
    max_emails = 100
    days = 7

    for arg in sys.argv[1:]:
        if arg == '--live':
            dry_run = False
        elif arg.startswith('--emails='):
            max_emails = int(arg.split('=')[1])
        elif arg.startswith('--days='):
            days = int(arg.split('=')[1])
        elif arg == '--dry-run':
            dry_run = True

    mode = "DRY RUN" if dry_run else "LIVE"
    logger.info("=" * 60)
    logger.info(f"NIGHTLY PROCESSING - {mode}")
    logger.info(f"Started at {datetime.now().isoformat()}")
    logger.info("=" * 60)

    # Start database run
    run_id = db.start_run()

    results = {}

    try:
        # 1. Email processing
        logger.info("\n--- EMAIL PROCESSING ---")
        results['email'] = run_email_processing(dry_run, max_emails, days)

        # 2. iMessage processing
        logger.info("\n--- iMESSAGE PROCESSING ---")
        results['imessage'] = run_imessage_processing(dry_run, days)

        # 3. Relationship follow-ups
        logger.info("\n--- RELATIONSHIP FOLLOW-UPS ---")
        results['relationships'] = generate_relationship_todos(dry_run)

        # Complete the run
        total_processed = results['email'].get('total', 0)
        db.complete_run(run_id, total_processed, 'completed')

    except Exception as e:
        logger.error(f"Nightly run failed: {e}")
        db.complete_run(run_id, 0, 'failed')
        results['error'] = str(e)

    # Log to sheet
    log_run_to_sheet(results, dry_run)

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Email: {results.get('email', {})}")
    logger.info(f"iMessage: {results.get('imessage', {})}")
    logger.info(f"Relationships: {results.get('relationships', {})}")
    logger.info(f"Mode: {mode}")
    logger.info(f"Completed at {datetime.now().isoformat()}")
    logger.info("=" * 60)

    # Exit code
    if 'error' in results:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
