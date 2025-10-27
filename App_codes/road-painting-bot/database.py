"""
Database module for Road Painting Bot
Handles all database operations using SQLite
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Optional, Dict
from contextlib import contextmanager
from config import Config

logger = logging.getLogger(__name__)


class Database:
    """Database manager for submissions"""

    def __init__(self, db_path: str = None):
        """Initialize database connection"""
        self.db_path = db_path or Config.DATABASE_PATH
        self.init_database()

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def init_database(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Create submissions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    photo_id TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    timestamp DATETIME NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    inspector_id INTEGER,
                    inspector_username TEXT,
                    decision_timestamp DATETIME,
                    rejection_reason TEXT,
                    notes TEXT
                )
            ''')

            # Create indexes for better query performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_user_id
                ON submissions(user_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_status
                ON submissions(status)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON submissions(timestamp DESC)
            ''')

            logger.info("Database initialized successfully")

    def create_submission(self, user_id: int, username: str, first_name: str,
                         last_name: str, photo_id: str, latitude: float,
                         longitude: float) -> int:
        """Create a new submission"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO submissions
                (user_id, username, first_name, last_name, photo_id,
                 latitude, longitude, timestamp, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            ''', (user_id, username, first_name, last_name, photo_id,
                  latitude, longitude, datetime.now()))

            submission_id = cursor.lastrowid
            logger.info(f"Created submission #{submission_id} for user {user_id}")
            return submission_id

    def get_submission(self, submission_id: int) -> Optional[Dict]:
        """Get submission by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM submissions WHERE id = ?', (submission_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_user_submissions(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get submissions by user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM submissions
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_pending_submissions(self, limit: int = 50) -> List[Dict]:
        """Get all pending submissions"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM submissions
                WHERE status = 'pending'
                ORDER BY timestamp ASC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def update_submission_status(self, submission_id: int, status: str,
                                 inspector_id: int, inspector_username: str,
                                 notes: str = None, rejection_reason: str = None) -> bool:
        """Update submission status (approve/reject)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE submissions
                SET status = ?,
                    inspector_id = ?,
                    inspector_username = ?,
                    decision_timestamp = ?,
                    notes = ?,
                    rejection_reason = ?
                WHERE id = ?
            ''', (status, inspector_id, inspector_username, datetime.now(),
                  notes, rejection_reason, submission_id))

            updated = cursor.rowcount > 0
            if updated:
                logger.info(f"Updated submission #{submission_id} to status: {status}")
            return updated

    def get_recent_decisions(self, limit: int = 10) -> List[Dict]:
        """Get recent approved/rejected submissions"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM submissions
                WHERE status IN ('approved', 'rejected')
                ORDER BY decision_timestamp DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self) -> Dict:
        """Get submission statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Total counts by status
            cursor.execute('''
                SELECT status, COUNT(*) as count
                FROM submissions
                GROUP BY status
            ''')
            status_counts = {row['status']: row['count'] for row in cursor.fetchall()}

            # Today's statistics
            cursor.execute('''
                SELECT status, COUNT(*) as count
                FROM submissions
                WHERE DATE(timestamp) = DATE('now')
                GROUP BY status
            ''')
            today_counts = {row['status']: row['count'] for row in cursor.fetchall()}

            # Approved today
            cursor.execute('''
                SELECT COUNT(*) as count
                FROM submissions
                WHERE status = 'approved'
                AND DATE(decision_timestamp) = DATE('now')
            ''')
            approved_today = cursor.fetchone()['count']

            return {
                'total_pending': status_counts.get('pending', 0),
                'total_approved': status_counts.get('approved', 0),
                'total_rejected': status_counts.get('rejected', 0),
                'total_submissions': sum(status_counts.values()),
                'today_submitted': sum(today_counts.values()),
                'today_approved': approved_today
            }

    def export_to_csv(self, filename: str = 'submissions_export.csv') -> str:
        """Export all submissions to CSV"""
        import csv
        from pathlib import Path

        # Create exports directory if it doesn't exist
        export_dir = Path('exports')
        export_dir.mkdir(exist_ok=True)
        filepath = export_dir / filename

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM submissions ORDER BY timestamp DESC')
            rows = cursor.fetchall()

            if not rows:
                return None

            # Write to CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)

                # Write header
                writer.writerow([description[0] for description in cursor.description])

                # Write data
                writer.writerows(rows)

        logger.info(f"Exported {len(rows)} submissions to {filepath}")
        return str(filepath)

    def get_submissions_near_location(self, latitude: float, longitude: float,
                                     radius_km: float = 5.0) -> List[Dict]:
        """Get submissions near a location (approximate using lat/lon differences)"""
        # Simple approximation: 1 degree ≈ 111 km
        lat_range = radius_km / 111.0
        lon_range = radius_km / (111.0 * abs(latitude / 90.0)) if latitude != 0 else lat_range

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM submissions
                WHERE latitude BETWEEN ? AND ?
                AND longitude BETWEEN ? AND ?
                ORDER BY timestamp DESC
            ''', (latitude - lat_range, latitude + lat_range,
                  longitude - lon_range, longitude + lon_range))

            return [dict(row) for row in cursor.fetchall()]


# Singleton instance
_db_instance = None


def get_db() -> Database:
    """Get database singleton instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
