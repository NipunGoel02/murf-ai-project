from __future__ import annotations

import asyncio
import json
import logging
import os
import sqlite3
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from livekit import api
from livekit.protocol.sip import CreateSIPParticipantRequest

from database import init_db


load_dotenv(".env.local")

logger = logging.getLogger("outbound_call")

DB_DIR = Path(__file__).resolve().parent.parent / "data"

DB_PATH = os.environ.get(
    "FINSAATHI_DB_PATH",
    str(DB_DIR / "users.db"),
)

DATA_DIR = DB_DIR

SIP_TRUNK_ID = "ST_PwsXbKNkrtAM"
AGENT_NAME = "my-agent"


def connect() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    return conn


def load_deadlines() -> dict[str, dict[str, Any]]:
    data_file = DATA_DIR / "scheme_deadlines.json"

    if not data_file.exists():
        logger.warning("scheme_deadlines.json not found: %s", data_file)
        return {}

    with data_file.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)

    deadlines = {}

    for deadline in raw.get("deadlines", []):
        scheme_id = str(
            deadline.get("scheme_id", "")
        ).strip().upper()

        if scheme_id:
            deadlines[scheme_id] = deadline

    return deadlines


def load_schemes() -> dict[str, dict[str, Any]]:
    data_file = DATA_DIR / "financial_schemes.json"

    if not data_file.exists():
        logger.warning("financial_schemes.json not found: %s", data_file)
        return {}

    with data_file.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)

    schemes = {}

    for scheme in raw.get("schemes", []):
        scheme_id = str(
            scheme.get("scheme_id", "")
        ).strip().upper()

        if scheme_id:
            schemes[scheme_id] = scheme

    return schemes


def should_trigger_outbound_call(
    *,
    demo_mode: bool,
    deadline: str | None,
    today: date | None,
    reminder_days: int,
    last_outbound_call: str | None,
) -> bool:

    if last_outbound_call:
        return False

    if demo_mode:
        return True

    if not deadline or not today:
        return False

    try:
        deadline_date = datetime.strptime(
            deadline,
            "%Y-%m-%d",
        ).date()

    except ValueError:
        logger.warning(
            "Invalid deadline format: %s",
            deadline,
        )
        return False

    if deadline_date < today:
        return False

    days_remaining = (
        deadline_date - today
    ).days

    return 0 <= days_remaining <= reminder_days


def timestamp() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
    )


def get_eligible_users() -> list[sqlite3.Row]:

    with connect() as conn:

        return list(
            conn.execute(
                """
                SELECT *
                FROM users
                WHERE eligibility_status = 'eligible'
                  AND COALESCE(outbound_opt_out, 0) = 0
                  AND COALESCE(phone_consent, 0) = 1
                  AND phone_number IS NOT NULL
                  AND phone_number != ''
                ORDER BY last_interaction DESC
                """
            )
        )


async def initiate_livekit_call(
    *,
    to_number: str,
    user_id: str,
    user_name: str,
    scheme_id: str,
    scheme_name: str,
    deadline: str,
    language: str | None,
    demo_mode: bool,
) -> Any:

    livekit_url = os.environ.get("LIVEKIT_URL")
    livekit_api_key = os.environ.get("LIVEKIT_API_KEY")
    livekit_api_secret = os.environ.get("LIVEKIT_API_SECRET")

    if not livekit_url:
        raise RuntimeError("LIVEKIT_URL is missing.")

    if not livekit_api_key:
        raise RuntimeError("LIVEKIT_API_KEY is missing.")

    if not livekit_api_secret:
        raise RuntimeError("LIVEKIT_API_SECRET is missing.")

    room_name = (
        f"finsaathi-outbound-"
        f"{user_id}-"
        f"{int(time.time())}"
    )

    metadata = json.dumps(
        {
            "call_type": "deadline_reminder",
            "user_id": user_id,
            "user_name": user_name,
            "phone_number": to_number,
            "scheme_id": scheme_id,
            "scheme_name": scheme_name,
            "deadline": deadline,
            "language": language or "hinglish",
            "demo_mode": demo_mode,
        }
    )

    logger.info(
        "Creating LiveKit agent dispatch for room %s",
        room_name,
    )

    async with api.LiveKitAPI(
        url=livekit_url,
        api_key=livekit_api_key,
        api_secret=livekit_api_secret,
    ) as lkapi:

        # First dispatch the existing my-agent into the room.
        dispatch = await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=AGENT_NAME,
                room=room_name,
                metadata=metadata,
            )
        )

        logger.info(
            "Agent dispatch created: %s",
            dispatch,
        )

        logger.info(
            "Creating SIP participant and calling %s",
            to_number,
        )

        request = CreateSIPParticipantRequest(
            sip_trunk_id=SIP_TRUNK_ID,
            sip_call_to=to_number,
            room_name=room_name,
            participant_identity=to_number,
            participant_name=user_name or "FinSaathi User",
            participant_metadata=metadata,
            wait_until_answered=True,
        )

        try:

            participant = (
                await lkapi.sip.create_sip_participant(
                    request
                )
            )

            logger.info(
                "LiveKit SIP participant created: %s",
                participant,
            )

            return participant

        except api.SipCallError as exc:

            logger.error(
                "SIP call failed: %s %s",
                exc.sip_status_code,
                exc.sip_status,
            )

            raise


async def run_outbound_checks() -> list[dict[str, Any]]:

    init_db()

    demo_mode = (
        os.environ.get(
            "DEMO_MODE",
            "false",
        )
        .strip()
        .lower()
        == "true"
    )

    reminder_days = int(
        os.environ.get(
            "REMINDER_DAYS",
            "7",
        )
    )

    logger.info("Checking eligible users...")
    logger.info("DEMO_MODE = %s", demo_mode)
    logger.info("REMINDER_DAYS = %s", reminder_days)

    deadlines = load_deadlines()
    schemes = load_schemes()

    logger.info(
        "Loaded %d deadlines",
        len(deadlines),
    )

    logger.info(
        "Loaded %d schemes",
        len(schemes),
    )

    users = get_eligible_users()

    logger.info(
        "Eligible users found: %d",
        len(users),
    )

    triggered = []

    for user in users:

        user_id = user["user_id"]

        logger.info(
            "Processing user: %s",
            user_id,
        )

        scheme_id = (
            user["scheme_id"] or ""
        ).strip().upper()

        if not scheme_id:
            logger.info(
                "User %s has no scheme_id - skipping.",
                user_id,
            )
            continue

        logger.info(
            "User scheme_id: %s",
            scheme_id,
        )

        if scheme_id not in deadlines:
            logger.info(
                "No deadline found for scheme_id %s - skipping.",
                scheme_id,
            )
            continue

        deadline_entry = deadlines[scheme_id]

        deadline = deadline_entry.get("deadline")

        logger.info(
            "Matched deadline: %s",
            deadline,
        )

        scheme_name = None

        if scheme_id in schemes:
            scheme_name = schemes[scheme_id].get("name")

        if not scheme_name:
            scheme_name = deadline_entry.get("name")

        should_call = should_trigger_outbound_call(
            demo_mode=demo_mode,
            deadline=deadline,
            today=date.today(),
            reminder_days=reminder_days,
            last_outbound_call=user[
                "last_outbound_call"
            ],
        )

        if not should_call:

            logger.info(
                "Deadline condition not met - skipping."
            )

            continue

        phone_number = (
            user["phone_number"] or ""
        ).strip()

        if not phone_number:
            logger.info(
                "Phone number missing - skipping."
            )
            continue

        if user["outbound_opt_out"]:
            logger.info(
                "User has opted out - skipping."
            )
            continue

        if user["phone_consent"] not in (1, True):
            logger.info(
                "User has not consented to reminder calls - skipping."
            )
            continue

        if user["last_outbound_call"]:
            logger.info(
                "Reminder already sent - skipping duplicate call."
            )
            continue

        logger.info(
            "Initiating LiveKit outbound AI call..."
        )

        try:

            participant = await initiate_livekit_call(
                to_number=phone_number,
                user_id=user_id,
                user_name=user["name"] or "friend",
                scheme_id=scheme_id,
                scheme_name=(
                    scheme_name
                    or "your financial scheme"
                ),
                deadline=(
                    deadline
                    or "the upcoming deadline"
                ),
                language=user[
                    "language_preference"
                ],
                demo_mode=demo_mode,
            )

        except Exception:

            logger.exception(
                "LiveKit outbound call failed for user %s",
                user_id,
            )

            continue

        participant_id = getattr(
            participant,
            "participant_identity",
            None,
        )

        logger.info(
            "Outbound AI call initiated successfully: %s",
            participant_id,
        )

        with connect() as conn:

            conn.execute(
                """
                UPDATE users
                SET last_outbound_call = ?,
                    last_interaction = ?
                WHERE user_id = ?
                """,
                (
                    timestamp(),
                    time.time(),
                    user_id,
                ),
            )

        triggered.append(
            {
                "user_id": user_id,
                "scheme_id": scheme_id,
                "phone_number": phone_number,
                "deadline": deadline,
                "demo_mode": demo_mode,
                "participant_identity": participant_id,
            }
        )

    return triggered


async def main():

    print(
        "OUTBOUND AI SCRIPT STARTED",
        flush=True,
    )

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s "
            "%(levelname)s "
            "%(message)s"
        ),
    )

    logger.info(
        "Starting outbound AI reminder checks"
    )

    try:

        triggered = await run_outbound_checks()

        logger.info(
            "Outbound check completed. "
            "Calls triggered: %d",
            len(triggered),
        )

        print(
            f"CHECK COMPLETED - "
            f"AI CALLS TRIGGERED: {len(triggered)}",
            flush=True,
        )

    except Exception as exc:

        logger.exception(
            "Outbound check failed"
        )

        print(
            f"ERROR: {exc}",
            flush=True,
        )


if __name__ == "__main__":
    asyncio.run(main())
