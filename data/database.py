"""
Database manager for Perceval.
Tracks events we've already seen and notified about to avoid duplicates.
"""
import sqlite3
import os
from datetime import datetime
from config.settings import DB_PATH


def get_db():
    """Get database connection, creating tables if needed."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            source_id TEXT NOT NULL,
            title TEXT,
            description TEXT,
            event_date TEXT,
            location TEXT,
            url TEXT,
            category TEXT,
            raw_text TEXT,
            notified_at TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(source, source_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scrape_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT,
            scraped_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    return conn


def event_exists(source: str, source_id: str) -> bool:
    """Check if we've already processed this event."""
    conn = get_db()
    cursor = conn.execute(
        "SELECT 1 FROM events WHERE source = ? AND source_id = ?",
        (source, source_id),
    )
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


def save_event(event: dict) -> bool:
    """Save an event to the database. Returns True if new, False if duplicate."""
    if event_exists(event["source"], event["source_id"]):
        return False

    conn = get_db()
    conn.execute(
        """
        INSERT INTO events (source, source_id, title, description, event_date,
                           location, url, category, raw_text, notified_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event["source"],
            event["source_id"],
            event.get("title", ""),
            event.get("description", ""),
            event.get("event_date", ""),
            event.get("location", ""),
            event.get("url", ""),
            event.get("category", ""),
            event.get("raw_text", ""),
            datetime.now().isoformat(),
        ),
    )
    conn.commit()
    conn.close()
    return True


def log_scrape(source: str, status: str, message: str = ""):
    """Log a scrape attempt."""
    conn = get_db()
    conn.execute(
        "INSERT INTO scrape_log (source, status, message) VALUES (?, ?, ?)",
        (source, status, message),
    )
    conn.commit()
    conn.close()


def get_recent_events(limit: int = 20) -> list:
    """Get recently notified events."""
    conn = get_db()
    cursor = conn.execute(
        "SELECT * FROM events ORDER BY created_at DESC LIMIT ?", (limit,)
    )
    events = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return events
