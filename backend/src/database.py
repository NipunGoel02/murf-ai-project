"""SQLite-backed persistence for caller profiles and human-support escalations.

Stores who the caller is (name, ID) along with a few facts relevant to the
Financial Services track.

The agent reads and writes through the functions in this module.

Privacy notes:
- Never store account numbers, card numbers, OTPs, or ID numbers.
- Only structured facts (schemes already checked, eligibility answers) are kept.
- Escalation summaries must not contain sensitive financial credentials.
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


# ============================================================
# EXISTING DAY 6 USERS TABLE
# ============================================================

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id              TEXT PRIMARY KEY,
    name                  TEXT NOT NULL,
    language_preference   TEXT,
    facts                 TEXT NOT NULL DEFAULT '{}',
    last_interaction      REAL NOT NULL,
    phone_number          TEXT,
    phone_consent         INTEGER,
    outbound_opt_out      INTEGER DEFAULT 0,
    eligibility_status    TEXT,
    scheme_id             TEXT,
    eligibility_checked_at TEXT,
    last_outbound_call    TEXT
);
"""


# ============================================================
# DAY 7 - HUMAN SUPPORT ESCALATIONS TABLE
# ============================================================

_ESCALATION_SCHEMA = """
CREATE TABLE IF NOT EXISTS escalations (
    request_id          TEXT PRIMARY KEY,
    user_id             TEXT NOT NULL,
    reason              TEXT NOT NULL,
    summary             TEXT NOT NULL,
    what_checked        TEXT,
    urgency             TEXT NOT NULL,
    language            TEXT,
    preferred_followup  TEXT,
    status              TEXT NOT NULL DEFAULT 'OPEN',
    created_at          TEXT NOT NULL,
    resolution          TEXT,
    resolved_at         TEXT
);
"""


def _connect() -> sqlite3.Connection:
    """Create and return a SQLite connection."""

    _DB_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(_DB_PATH)

    conn.row_factory = sqlite3.Row

    return conn


def _normalize_bool(value: object) -> int | None:
    """Convert common boolean-like values into SQLite integer values."""

    if value is None:
        return None

    if isinstance(value, bool):
        return int(value)

    if isinstance(value, (int, float)):
        return int(value)

    if isinstance(value, str):

        normalized = value.strip().lower()

        if normalized in {
            "1",
            "true",
            "yes",
            "y",
            "consent",
            "consented",
        }:
            return 1

        if normalized in {
            "0",
            "false",
            "no",
            "n",
            "decline",
            "stop",
        }:
            return 0

    return None


def _ensure_schema() -> None:
    """Create all required database tables and missing Day 6 columns."""

    with _connect() as conn:

        # Existing Day 6 users table
        conn.execute(_SCHEMA)

        # New Day 7 escalations table
        conn.execute(_ESCALATION_SCHEMA)

        # Check existing columns in users table
        existing_columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(users)")
        }

        # Existing Day 6 columns
        for column_name, ddl in [
            (
                "phone_number",
                "ALTER TABLE users ADD COLUMN phone_number TEXT",
            ),
            (
                "phone_consent",
                "ALTER TABLE users ADD COLUMN phone_consent INTEGER",
            ),
            (
                "outbound_opt_out",
                "ALTER TABLE users ADD COLUMN outbound_opt_out INTEGER DEFAULT 0",
            ),
            (
                "eligibility_status",
                "ALTER TABLE users ADD COLUMN eligibility_status TEXT",
            ),
            (
                "scheme_id",
                "ALTER TABLE users ADD COLUMN scheme_id TEXT",
            ),
            (
                "eligibility_checked_at",
                "ALTER TABLE users ADD COLUMN eligibility_checked_at TEXT",
            ),
            (
                "last_outbound_call",
                "ALTER TABLE users ADD COLUMN last_outbound_call TEXT",
            ),
        ]:

            if column_name not in existing_columns:
                conn.execute(ddl)

        conn.commit()


def init_db() -> None:
    """Create the database and all required tables."""

    _DB_DIR.mkdir(parents=True, exist_ok=True)

    _ensure_schema()

    logger.info(
        "Database ready at %s",
        _DB_PATH,
    )


# ============================================================
# EXISTING DAY 6 USER FUNCTIONS
# ============================================================

def find_user(user_id: str) -> dict | None:
    """Return a saved profile for a caller, or None if unknown."""

    if not user_id:
        return None

    _ensure_schema()

    with _connect() as conn:

        row = conn.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()

    if row is None:
        return None

    try:

        facts = json.loads(
            row["facts"] or "{}"
        )

    except (
        json.JSONDecodeError,
        TypeError,
    ):

        facts = {}

    if (
        row["phone_number"]
        and "phone_number" not in facts
    ):
        facts["phone_number"] = row["phone_number"]

    if (
        row["phone_consent"] is not None
        and "phone_consent" not in facts
    ):
        facts["phone_consent"] = bool(
            row["phone_consent"]
        )

    if (
        row["outbound_opt_out"] is not None
        and "outbound_opt_out" not in facts
    ):
        facts["outbound_opt_out"] = bool(
            row["outbound_opt_out"]
        )

    if (
        row["eligibility_status"]
        and "eligibility_status" not in facts
    ):
        facts["eligibility_status"] = (
            row["eligibility_status"]
        )

    if (
        row["scheme_id"]
        and "scheme_id" not in facts
    ):
        facts["scheme_id"] = row["scheme_id"]

    if (
        row["eligibility_checked_at"]
        and "eligibility_checked_at" not in facts
    ):
        facts["eligibility_checked_at"] = (
            row["eligibility_checked_at"]
        )

    if (
        row["last_outbound_call"]
        and "last_outbound_call" not in facts
    ):
        facts["last_outbound_call"] = (
            row["last_outbound_call"]
        )

    return {
        "user_id": row["user_id"],
        "name": row["name"],
        "language_preference": row["language_preference"],
        "facts": facts,
        "last_interaction": row["last_interaction"],
        "phone_number": row["phone_number"],
        "phone_consent": (
            bool(row["phone_consent"])
            if row["phone_consent"] is not None
            else None
        ),
        "outbound_opt_out": (
            bool(row["outbound_opt_out"])
            if row["outbound_opt_out"] is not None
            else None
        ),
        "eligibility_status": row["eligibility_status"],
        "scheme_id": row["scheme_id"],
        "eligibility_checked_at": row[
            "eligibility_checked_at"
        ],
        "last_outbound_call": row[
            "last_outbound_call"
        ],
    }


def save_user(
    user_id: str,
    name: str,
    language_preference: str | None = None,
    facts: dict | None = None,
    phone_number: str | None = None,
    phone_consent: bool | None = None,
    outbound_opt_out: bool | None = None,
    eligibility_status: str | None = None,
    scheme_id: str | None = None,
    eligibility_checked_at: str | None = None,
    last_outbound_call: str | None = None,
) -> None:
    """Insert a new caller profile or update an existing one."""

    if not user_id or not name:
        return

    _ensure_schema()

    facts_payload = dict(facts or {})

    if phone_number is not None:
        facts_payload["phone_number"] = phone_number

    if phone_consent is not None:
        facts_payload["phone_consent"] = phone_consent

    if outbound_opt_out is not None:
        facts_payload["outbound_opt_out"] = (
            outbound_opt_out
        )

    if eligibility_status is not None:
        facts_payload["eligibility_status"] = (
            eligibility_status
        )

    if scheme_id is not None:
        facts_payload["scheme_id"] = scheme_id

    if eligibility_checked_at is not None:
        facts_payload[
            "eligibility_checked_at"
        ] = eligibility_checked_at

    if last_outbound_call is not None:
        facts_payload[
            "last_outbound_call"
        ] = last_outbound_call

    now = time.time()

    with _connect() as conn:

        conn.execute(
            """
            INSERT INTO users (
                user_id,
                name,
                language_preference,
                facts,
                last_interaction,
                phone_number,
                phone_consent,
                outbound_opt_out,
                eligibility_status,
                scheme_id,
                eligibility_checked_at,
                last_outbound_call
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )

            ON CONFLICT(user_id) DO UPDATE SET
                name = excluded.name,
                language_preference = excluded.language_preference,
                facts = excluded.facts,
                last_interaction = excluded.last_interaction,
                phone_number = excluded.phone_number,
                phone_consent = excluded.phone_consent,
                outbound_opt_out = excluded.outbound_opt_out,
                eligibility_status = excluded.eligibility_status,
                scheme_id = excluded.scheme_id,
                eligibility_checked_at = excluded.eligibility_checked_at,
                last_outbound_call = excluded.last_outbound_call
            """,
            (
                user_id,
                name,
                language_preference,
                json.dumps(facts_payload),
                now,
                facts_payload.get(
                    "phone_number"
                ),
                _normalize_bool(
                    facts_payload.get(
                        "phone_consent"
                    )
                ),
                _normalize_bool(
                    facts_payload.get(
                        "outbound_opt_out"
                    )
                ),
                facts_payload.get(
                    "eligibility_status"
                ),
                facts_payload.get(
                    "scheme_id"
                ),
                facts_payload.get(
                    "eligibility_checked_at"
                ),
                facts_payload.get(
                    "last_outbound_call"
                ),
            ),
        )


    logger.info(
        "Saved profile for user %s (%s)",
        user_id,
        name,
    )


def update_facts(
    user_id: str,
    facts: dict,
) -> None:
    """Merge new facts into a caller's existing profile."""

    if not user_id or not facts:
        return

    _ensure_schema()

    profile = find_user(user_id)

    if profile is None:
        return

    merged = dict(
        profile["facts"]
    )

    merged.update(facts)

    phone_number = merged.get(
        "phone_number"
    )

    phone_consent = _normalize_bool(
        merged.get("phone_consent")
    )

    outbound_opt_out = _normalize_bool(
        merged.get("outbound_opt_out")
    )

    eligibility_status = merged.get(
        "eligibility_status"
    )

    scheme_id = merged.get(
        "scheme_id"
    )

    eligibility_checked_at = merged.get(
        "eligibility_checked_at"
    )

    last_outbound_call = merged.get(
        "last_outbound_call"
    )

    with _connect() as conn:

        conn.execute(
            """
            UPDATE users

            SET
                facts = ?,
                last_interaction = ?,
                phone_number = ?,
                phone_consent = ?,
                outbound_opt_out = ?,
                eligibility_status = ?,
                scheme_id = ?,
                eligibility_checked_at = ?,
                last_outbound_call = ?

            WHERE user_id = ?
            """,
            (
                json.dumps(merged),
                time.time(),
                phone_number,
                phone_consent,
                outbound_opt_out,
                eligibility_status,
                scheme_id,
                eligibility_checked_at,
                last_outbound_call,
                user_id,
            ),
        )

    logger.info(
        "Updated facts for user %s",
        user_id,
    )


# ============================================================
# DAY 7 - ESCALATION FUNCTIONS
# ============================================================

def create_escalation(
    request_id: str,
    user_id: str,
    reason: str,
    summary: str,
    what_checked: str,
    urgency: str,
    language: str | None,
    preferred_followup: str | None,
    created_at: str,
) -> None:
    """
    Create a new human-support escalation.

    This function only stores structured escalation information.
    Sensitive credentials such as OTP, PIN, CVV, passwords,
    card numbers, and account numbers must never be passed here.
    """

    if not request_id:
        raise ValueError(
            "request_id is required"
        )

    if not user_id:
        raise ValueError(
            "user_id is required"
        )

    if not reason:
        raise ValueError(
            "reason is required"
        )

    if not summary:
        raise ValueError(
            "summary is required"
        )

    if not urgency:
        urgency = "MEDIUM"

    if not created_at:
        created_at = str(
            time.time()
        )

    _ensure_schema()

    with _connect() as conn:

        conn.execute(
            """
            INSERT INTO escalations (
                request_id,
                user_id,
                reason,
                summary,
                what_checked,
                urgency,
                language,
                preferred_followup,
                status,
                created_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?
            )
            """,
            (
                request_id,
                user_id,
                reason,
                summary,
                what_checked,
                urgency,
                language,
                preferred_followup,
                created_at,
            ),
        )

    logger.info(
        "Created human-support escalation %s for user %s",
        request_id,
        user_id,
    )


def get_escalations(
    status: str | None = None,
) -> list[dict]:
    """
    Return human-support escalation requests.

    If status is provided, only requests with that status
    are returned.
    """

    _ensure_schema()

    with _connect() as conn:

        if status:

            rows = conn.execute(
                """
                SELECT *
                FROM escalations
                WHERE status = ?
                ORDER BY created_at DESC
                """,
                (status,),
            ).fetchall()

        else:

            rows = conn.execute(
                """
                SELECT *
                FROM escalations
                ORDER BY created_at DESC
                """
            ).fetchall()

    return [
        dict(row)
        for row in rows
    ]


def get_escalation(
    request_id: str,
) -> dict | None:
    """Return one escalation by reference ID."""

    if not request_id:
        return None

    _ensure_schema()

    with _connect() as conn:

        row = conn.execute(
            """
            SELECT *
            FROM escalations
            WHERE request_id = ?
            """,
            (request_id,),
        ).fetchone()

    if row is None:
        return None

    return dict(row)


def update_escalation(
    request_id: str,
    status: str,
    resolution: str | None = None,
) -> bool:
    """
    Update an escalation status.

    Supported status values:

    OPEN
    IN_PROGRESS
    RESOLVED
    """

    allowed_statuses = {
        "OPEN",
        "IN_PROGRESS",
        "RESOLVED",
    }

    status = status.upper().strip()

    if status not in allowed_statuses:
        raise ValueError(
            f"Invalid escalation status: {status}"
        )

    if not request_id:
        return False

    _ensure_schema()

    with _connect() as conn:

        if status == "RESOLVED":

            resolved_at = str(
                time.time()
            )

            cursor = conn.execute(
                """
                UPDATE escalations

                SET
                    status = ?,
                    resolution = ?,
                    resolved_at = ?

                WHERE request_id = ?
                """,
                (
                    status,
                    resolution,
                    resolved_at,
                    request_id,
                ),
            )

        else:

            cursor = conn.execute(
                """
                UPDATE escalations

                SET
                    status = ?

                WHERE request_id = ?
                """,
                (
                    status,
                    request_id,
                ),
            )

        conn.commit()

    updated = cursor.rowcount > 0

    if updated:

        logger.info(
            "Updated escalation %s -> %s",
            request_id,
            status,
        )

    return updated
