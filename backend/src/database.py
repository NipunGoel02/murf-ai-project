"""SQLite-backed persistence for caller profiles.

Stores who the caller is (name, ID) along with a few facts relevant to the
Financial Services track. The agent reads and writes through the functions in
this module — never through the prompt directly.

Privacy notes:
- Never store account numbers, card numbers, OTPs, or ID numbers.
- Only structured facts (schemes already checked, eligibility answers) are kept.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
from pathlib import Path

logger = logging.getLogger("agent")

# DB file lives in backend/data/users.db
_DB_DIR = Path(__file__).resolve().parent.parent / "data"
_DB_PATH = os.environ.get("FINSAATHI_DB_PATH", str(_DB_DIR / "users.db"))

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id              TEXT PRIMARY KEY,
    name                 TEXT NOT NULL,
    language_preference  TEXT,
    facts                TEXT NOT NULL DEFAULT '{}',
    last_interaction     REAL NOT NULL
);
"""


def _connect() -> sqlite3.Connection:
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the database and users table if they do not exist."""
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    with _connect() as conn:
        conn.execute(_SCHEMA)
    logger.info("Database ready at %s", _DB_PATH)


def find_user(user_id: str) -> dict | None:
    """Return a saved profile for a caller, or None if unknown."""
    if not user_id:
        return None
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
    if row is None:
        return None
    try:
        facts = json.loads(row["facts"] or "{}")
    except (json.JSONDecodeError, TypeError):
        facts = {}
    return {
        "user_id": row["user_id"],
        "name": row["name"],
        "language_preference": row["language_preference"],
        "facts": facts,
        "last_interaction": row["last_interaction"],
    }


def save_user(
    user_id: str,
    name: str,
    language_preference: str | None = None,
    facts: dict | None = None,
) -> None:
    """Insert a new caller profile, or update an existing one."""
    if not user_id or not name:
        return
    now = time.time()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO users (user_id, name, language_preference, facts, last_interaction)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name = excluded.name,
                language_preference = excluded.language_preference,
                facts = excluded.facts,
                last_interaction = excluded.last_interaction
            """,
            (user_id, name, language_preference, json.dumps(facts or {}), now),
        )
    logger.info("Saved profile for user %s (%s)", user_id, name)


def update_facts(user_id: str, facts: dict) -> None:
    """Merge new facts into a caller's existing profile."""
    if not user_id or not facts:
        return
    profile = find_user(user_id)
    if profile is None:
        return
    merged = dict(profile["facts"])
    merged.update(facts)
    with _connect() as conn:
        conn.execute(
            "UPDATE users SET facts = ?, last_interaction = ? WHERE user_id = ?",
            (json.dumps(merged), time.time(), user_id),
        )
    logger.info("Updated facts for user %s", user_id)
