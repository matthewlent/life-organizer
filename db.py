#!/usr/bin/env python3
"""
SQLite database for tracking processed emails and cursors.
"""

import os
import sqlite3
from datetime import datetime
from typing import Optional

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, 'life_organizer.db')


def get_connection():
    """Get SQLite connection with row factory."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    # Processed emails table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_emails (
            email_id TEXT PRIMARY KEY,
            processed_at TEXT NOT NULL,
            action TEXT NOT NULL,
            category TEXT,
            project TEXT,
            destination TEXT,
            notes TEXT
        )
    ''')

    # Cursors for tracking progress
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cursors (
            name TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')

    # Processing runs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            emails_processed INTEGER DEFAULT 0,
            status TEXT DEFAULT 'running'
        )
    ''')

    conn.commit()
    conn.close()


def is_processed(email_id: str) -> bool:
    """Check if email has been processed."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM processed_emails WHERE email_id = ?', (email_id,))
    result = cursor.fetchone() is not None
    conn.close()
    return result


def mark_processed(email_id: str, action: str, category: str = None,
                   project: str = None, destination: str = None, notes: str = None):
    """Mark email as processed."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO processed_emails
        (email_id, processed_at, action, category, project, destination, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (email_id, datetime.now().isoformat(), action, category, project, destination, notes))
    conn.commit()
    conn.close()


def get_cursor(name: str) -> Optional[str]:
    """Get cursor value."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM cursors WHERE name = ?', (name,))
    row = cursor.fetchone()
    conn.close()
    return row['value'] if row else None


def set_cursor(name: str, value: str):
    """Set cursor value."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO cursors (name, value, updated_at)
        VALUES (?, ?, ?)
    ''', (name, value, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def start_run() -> int:
    """Start a new processing run."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO runs (started_at, status) VALUES (?, 'running')
    ''', (datetime.now().isoformat(),))
    run_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return run_id


def complete_run(run_id: int, emails_processed: int, status: str = 'completed'):
    """Complete a processing run."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE runs SET completed_at = ?, emails_processed = ?, status = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), emails_processed, status, run_id))
    conn.commit()
    conn.close()


def get_stats() -> dict:
    """Get processing statistics."""
    conn = get_connection()
    cursor = conn.cursor()

    # Total processed
    cursor.execute('SELECT COUNT(*) as count FROM processed_emails')
    total = cursor.fetchone()['count']

    # By action
    cursor.execute('''
        SELECT action, COUNT(*) as count FROM processed_emails GROUP BY action
    ''')
    by_action = {row['action']: row['count'] for row in cursor.fetchall()}

    # Recent runs
    cursor.execute('''
        SELECT * FROM runs ORDER BY id DESC LIMIT 5
    ''')
    recent_runs = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return {
        'total_processed': total,
        'by_action': by_action,
        'recent_runs': recent_runs
    }


# Initialize database on import
init_db()
