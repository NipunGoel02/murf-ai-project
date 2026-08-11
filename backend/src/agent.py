import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    UserInputTranscribedEvent,
    cli,
    function_tool,
    room_io,
    tokenize,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from database import find_user, init_db, save_user, update_facts
from prompt import SYSTEM_PROMPT


logger = logging.getLogger("agent")


def _load_financial_schemes() -> dict[str, dict]:
    data_file = (
        Path(__file__).resolve().parent.parent
        / "data"
        / "financial_schemes.json"
    )

    try:
        with open(data_file, "r", encoding="utf-8") as fh:
            raw = json.load(fh)

    except FileNotFoundError as exc:
        raise FileNotFoundError(
            "Financial schemes dataset not found."
        ) from exc

    except json.JSONDecodeError as exc:
        raise ValueError(
            "Financial schemes dataset is not valid JSON."
        ) from exc

    schemes = {}

    for scheme in raw.get("schemes", []):
        scheme_id = str(
            scheme.get("scheme_id", "")
        ).strip().upper()

        if scheme_id:
            schemes[scheme_id] = scheme

    return schemes


def _normalize_scheme_name(text: str) -> str:
    return re.sub(
        r"[^a-z0-9]",
        "",
        text.strip().lower()
    )


def _find_scheme(
    scheme_name: str,
    schemes: dict[str, dict]
) -> dict | None:

    normalized_query = _normalize_scheme_name(
        scheme_name
    )

    if not normalized_query:
        return None

    for scheme_id, scheme in schemes.items():

        normalized_id = _normalize_scheme_name(
            scheme_id
        )

        normalized_name = _normalize_scheme_name(
            scheme.get("name", "")
        )

        if normalized_query == normalized_id:
            return scheme

        if normalized_query == normalized_name:
            return scheme

        if normalized_query in normalized_name:
            return scheme

        if normalized_id in normalized_query:
            return scheme

    return None


load_dotenv(".env.local")


class Assistant(Agent):

    def __init__(self) -> None:

        super().__init__(
            instructions=SYSTEM_PROMPT
        )

        init_db()

    @staticmethod
    def _caller_user_id(
        context: RunContext
    ) -> str | None:

        """
        Resolve the caller's identity.

        Uses the session's RoomIO linked participant
        and falls back to room participants.
        """

        room_io_obj = None

        try:

            room_io_obj = getattr(
                context.session,
                "room_io",
                None
            )

            if room_io_obj is not None:

                participant = getattr(
                    room_io_obj,
                    "linked_participant",
                    None
                )

                if participant is not None:
                    return participant.identity

        except Exception as exc:

            logger.debug(
                "Could not get linked participant: %s",
                exc
            )

        try:

            room = getattr(
                room_io_obj,
                "room",
                None
            )

            if room is None:
                room = getattr(
                    context,
                    "room",
                    None
                )

            if room is not None:

                for participant in room.participants.values():

                    if (
                        participant.kind
                        != rtc.ParticipantKind.PARTICIPANT_KIND_AGENT
                    ):
                        return participant.identity

                for participant in room.remote_participants.values():

                    return participant.identity

        except Exception as exc:

            logger.debug(
                "Could not scan room participants: %s",
                exc
            )

        return None

    @function_tool
    async def lookup_user(
        self,
        context: RunContext
    ) -> dict | None:

        """
        Look up a caller's saved profile.

        Call this at the start of every conversation.
        """

        user_id = self._caller_user_id(context)

        logger.info(
            "lookup_user - resolved user_id = %r",
            user_id
        )

        profile = find_user(user_id)

        logger.info(
            "lookup_user(%s) -> %s",
            user_id,
            profile
        )

        return profile

    @function_tool
    async def save_user(
        self,
        context: RunContext,
        name: str,
        facts: str,
        language_preference: str | None = None,
        phone_number: str | None = None,
        phone_consent: bool | None = None,
    ) -> str:

        """
        Save or update a caller's profile.

        Only call this AFTER the caller has explicitly agreed
        to be remembered.

        For outbound calls, only save the phone number when
        the caller explicitly gives consent.

        Never store:
        - OTP
        - PIN
        - CVV
        - Password
        - Bank account number
        - Government ID number
        """

        user_id = self._caller_user_id(context)

        logger.info(
            "save_user - resolved user_id = %r",
            user_id
        )

        if not user_id:

            logger.warning(
                "save_user failed: caller identity not found"
            )

            return (
                "I could not identify the caller, "
                "so I did not save anything."
            )

        try:

            facts_dict = (
                json.loads(facts)
                if facts
                else {}
            )

            if not isinstance(
                facts_dict,
                dict
            ):
                facts_dict = {}

        except json.JSONDecodeError:

            logger.warning(
                "Invalid facts JSON received: %s",
                facts
            )

            facts_dict = {}

        if phone_number:

            phone_number = phone_number.strip()

            if re.fullmatch(
                r"\d{10}",
                phone_number
            ):

                phone_number = (
                    "+91" + phone_number
                )

            elif re.fullmatch(
                r"91\d{10}",
                phone_number
            ):

                phone_number = (
                    "+" + phone_number
                )

            elif phone_number.startswith("+91"):

                phone_number = (
                    "+91"
                    + re.sub(
                        r"\D",
                        "",
                        phone_number[3:]
                    )
                )

            facts_dict["phone_number"] = (
                phone_number
            )

        if phone_consent is not None:

            facts_dict["phone_consent"] = bool(
                phone_consent
            )

        logger.info(
            "Prepared facts for save: %s",
            facts_dict
        )

        existing = find_user(user_id)

        try:

            if existing is None:

                save_user(
                    user_id=user_id,
                    name=name,
                    language_preference=(
                        language_preference
                    ),
                    facts=facts_dict,
                )

                logger.info(
                    "Created new profile for %s",
                    user_id
                )

            else:

                merged_facts = dict(
                    existing.get("facts") or {}
                )

                merged_facts.update(
                    facts_dict
                )

                if (
                    "phone_number"
                    not in facts_dict
                    and existing.get(
                        "phone_number"
                    )
                ):

                    merged_facts[
                        "phone_number"
                    ] = existing[
                        "phone_number"
                    ]

                if (
                    "phone_consent"
                    not in facts_dict
                    and existing.get(
                        "phone_consent"
                    )
                    is not None
                ):

                    merged_facts[
                        "phone_consent"
                    ] = existing[
                        "phone_consent"
                    ]

                save_user(
                    user_id=user_id,
                    name=(
                        name
                        or existing["name"]
                    ),
                    language_preference=(
                        language_preference
                        or existing[
                            "language_preference"
                        ]
                    ),
                    facts=merged_facts,
                )

                logger.info(
                    "Updated existing profile for %s",
                    user_id
                )

            saved_profile = find_user(
                user_id
            )

            if saved_profile is None:

                logger.error(
                    "Verification failed: "
                    "profile not found after save"
                )

                return (
                    "I could not verify the profile save. "
                    "Please try again."
                )

            if phone_number:

                saved_phone = (
                    saved_profile.get(
                        "phone_number"
                    )
                )

                if saved_phone != phone_number:

                    logger.error(
                        "Phone number verification failed. "
                        "Expected=%s Actual=%s",
                        phone_number,
                        saved_phone,
                    )

                    return (
                        "I could not verify the phone number "
                        "was saved. Please try again."
                    )

            logger.info(
                "save_user SUCCESS: user=%s name=%s phone=%s consent=%s",
                user_id,
                name,
                saved_profile.get(
                    "phone_number"
                ),
                saved_profile.get(
                    "phone_consent"
                ),
            )

            return f"Saved profile for {name}."

        except Exception:

            logger.exception(
                "save_user failed for %s",
                user_id
            )

            return (
                "I could not save your information "
                "because of a database error. "
                "Please try again."
            )

    @function_tool
    async def check_scheme_eligibility(
        self,
        context: RunContext,
        scheme_name: str,
        citizenship: str,
        age: int,
        has_savings_bank_account: bool | None = None,
        auto_debit_available: bool | None = None,
        business_purpose: str | None = None,
    ) -> dict:

        """
        Check eligibility for a supported financial scheme.
        """

        try:

            schemes = _load_financial_schemes()

        except Exception as exc:

            logger.error(
                "Scheme eligibility tool failed loading dataset: %s",
                exc
            )

            return {
                "success": False,
                "error": (
                    "Dataset unavailable. "
                    "Please try again later or check "
                    "the official Government of India source."
                ),
            }

        scheme = _find_scheme(
            scheme_name,
            schemes
        )

        if scheme is None:

            logger.info(
                "Unsupported scheme requested: %s",
                scheme_name
            )

            return {
                "success": False,
                "error": (
                    "Unsupported scheme. Supported schemes "
                    "are PMMY, PMJJBY, and PMSBY."
                ),
            }

        scheme_id = scheme[
            "scheme_id"
        ].upper()

        required_missing = []

        if (
            scheme_id == "PMMY"
            and not business_purpose
        ):

            required_missing.append(
                "business_purpose"
            )

        if scheme_id in {
            "PMJJBY",
            "PMSBY"
        }:

            if has_savings_bank_account is None:

                required_missing.append(
                    "has_savings_bank_account"
                )

            if auto_debit_available is None:

                required_missing.append(
                    "auto_debit_available"
                )

        if required_missing:

            logger.info(
                "Scheme eligibility tool missing "
                "required inputs: %s for %s",
                required_missing,
                scheme_id,
            )

            return {
                "success": False,
                "error": (
                    "Missing required eligibility information. "
                    "Please provide the missing details before "
                    "checking the scheme."
                ),
            }

        normalized_citizenship = (
            citizenship.strip().lower()
            if citizenship
            else ""
        )

        is_indian_citizen = any(
            token in normalized_citizenship
            for token in [
                "indian",
                "hindustan",
                "bharatiya",
                "haan",
                "yes",
                "y",
                "true",
            ]
        )

        failures = []

        if not is_indian_citizen:

            failures.append(
                "The applicant does not appear "
                "to be an Indian citizen."
            )

        minimum_age = scheme[
            "eligibility"
        ].get("minimum_age")

        maximum_age = scheme[
            "eligibility"
        ].get("maximum_age")

        if (
            minimum_age is not None
            and age < minimum_age
        ):

            failures.append(
                f"The applicant must be at least "
                f"{minimum_age} years old."
            )

        if (
            maximum_age is not None
            and age > maximum_age
        ):

            failures.append(
                f"The applicant must be no older "
                f"than {maximum_age} years old."
            )

        if scheme_id in {
            "PMJJBY",
            "PMSBY"
        }:

            if not has_savings_bank_account:

                failures.append(
                    "A valid savings bank account "
                    "with auto-debit capability is required."
                )

            if not auto_debit_available:

                failures.append(
                    "Auto-debit authorization from "
                    "the savings bank account is required."
                )

        if scheme_id == "PMMY":

            normalized_purpose = (
                business_purpose.strip().lower()
                if business_purpose
                else ""
            )

            business_indicators = [
                "business",
                "enterprise",
                "self-employ",
                "shop",
                "vendor",
                "trader",
                "small business",
                "micro business",
                "manufacturing",
                "service",
                "sales",
                "startup",
                "entrepreneur",
                "udyam",
            ]

            if not any(
                keyword in normalized_purpose
                for keyword in business_indicators
            ):

                failures.append(
                    "The scheme is for business purposes "
                    "or non-farm enterprise activities only."
                )

        eligible = len(failures) == 0

        result = {
            "success": True,
            "scheme_id": scheme_id,
            "scheme_name": scheme["name"],
            "eligible": eligible,
            "reasons": (
                failures
                if failures
                else [
                    "The provided information satisfies "
                    "the listed eligibility criteria."
                ]
            ),
            "checked_criteria": {
                "citizenship": citizenship,
                "age": age,
                "has_savings_bank_account":
                    has_savings_bank_account,
                "auto_debit_available":
                    auto_debit_available,
                "business_purpose":
                    business_purpose,
            },
            "source": scheme.get("source"),
            "source_url": scheme.get(
                "source_url"
            ),
            "last_verified": scheme.get(
                "last_verified"
            ),
        }

        logger.info(
            "Scheme eligibility check completed "
            "for %s: eligible=%s",
            scheme_id,
            eligible,
        )

        user_id = self._caller_user_id(
            context
        )

        if user_id:

            profile = find_user(
                user_id
            )

            name = (
                (profile or {}).get("name")
                or "caller"
            )

            eligibility_payload = {
                "scheme_id": scheme_id,
                "eligibility_status": (
                    "eligible"
                    if eligible
                    else "ineligible"
                ),
                "eligibility_checked_at": (
                    datetime.now(
                        timezone.utc
                    )
                    .replace(
                        microsecond=0
                    )
                    .isoformat()
                ),
            }

            if profile is None:

                save_user(
                    user_id,
                    name,
                    None,
                    eligibility_payload,
                )

            else:

                update_facts(
                    user_id,
                    eligibility_payload
                )

        return result


server = AgentServer()


def prewarm(proc: JobProcess):

    proc.userdata["vad"] = (
        silero.VAD.load()
    )


server.setup_fnc = prewarm


@server.rtc_session(
    agent_name="my-agent"
)
async def my_agent(
    ctx: JobContext
):

    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # -------------------------------------------------
    # OUTBOUND CALL METADATA
    # -------------------------------------------------

    outbound_metadata = {}

    try:

        if ctx.job.metadata:

            outbound_metadata = json.loads(
                ctx.job.metadata
            )

    except Exception:

        logger.exception(
            "Could not parse outbound call metadata"
        )

    is_outbound = (
        outbound_metadata.get(
            "call_type"
        )
        == "deadline_reminder"
    )

    logger.info(
        "Outbound call=%s metadata=%s",
        is_outbound,
        outbound_metadata,
    )

    # -------------------------------------------------
    # AGENT SESSION
    # -------------------------------------------------

    session = AgentSession(

        stt=deepgram.STT(
            model="nova-3",
            language="multi",
        ),

        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),

        tts=murf.TTS(
            voice="hi-IN-anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(
                min_sentence_len=2
            ),
            text_pacing=True,
        ),

        turn_detection=MultilingualModel(),

        vad=ctx.proc.userdata["vad"],

        preemptive_generation=True,
    )

    @session.on(
        "user_input_transcribed"
    )
    def on_user_input_transcribed(
        ev: UserInputTranscribedEvent
    ):

        asyncio.create_task(
            handle_user_input_transcribed(ev)
        )

    async def handle_user_input_transcribed(
        ev: UserInputTranscribedEvent
    ):

        transcript = (
            ev.text.strip().lower()
        )

        if not transcript:
            return

        has_devanagari = any(
            "\u0900" <= ch <= "\u097F"
            for ch in transcript
        )

        hindi_keywords = {

            "namaste",
            "namaskar",
            "helloji",
            "ramram",
            "pranam",

            "main",
            "mai",
            "mein",
            "me",
            "mera",
            "meri",
            "mere",
            "mujhe",
            "mujhko",
            "hum",
            "ham",
            "hamara",
            "hamari",
            "aap",
            "ap",
            "tum",
            "tumhara",
            "tumhari",
            "tumhe",
            "bhai",
            "behen",
            "sir",
            "madam",
            "ji",

            "hai",
            "hu",
            "ho",
            "tha",
            "thi",
            "the",
            "hoga",
            "hogi",
            "haan",
            "han",
            "ha",
            "nahi",
            "nahin",
            "na",
            "acha",
            "achha",
            "theek",
            "thik",
            "bilkul",
            "jarur",
            "zarur",
            "please",

            "kya",
            "kaise",
            "kab",
            "kahan",
            "kidhar",
            "kyu",
            "kyon",
            "kaun",
            "kis",
            "kitna",
            "kitni",
            "kitne",
            "kaunsa",

            "aaj",
            "kal",
            "abhi",
            "subah",
            "dopahar",
            "shaam",
            "raat",
            "ab",
            "baad",
            "pehle",
            "phir",

            "loan",
            "loans",
            "paisa",
            "paise",
            "bank",
            "scheme",
            "yojana",
            "insurance",
            "payment",
            "emi",
            "saving",
            "savings",

            "karna",
            "karni",
            "karo",
            "kar",
            "book",
            "cancel",
            "reschedule",
            "milna",
            "jana",
            "aana",
            "dekhna",
            "batana",
            "sunna",
            "madad",
            "help",
            "chahiye",
            "hona",
            "bolna",
            "boliye",
            "bataye",

            "maa",
            "papa",
            "pitaji",
            "mataji",
            "beta",
            "beti",
            "uncle",
            "aunty",
            "dada",
            "dadi",
            "nana",
            "nani",
            "wife",
            "husband",
            "bacha",
            "baccha",

            "haanji",
            "jihaan",
            "shukriya",
            "dhanyawad",
            "kripya",
            "urgent",
            "jaldi",
        }

        words = set(
            re.findall(
                r"[a-zA-Z\u0900-\u097F]+",
                transcript,
            )
        )

        matched_words = words.intersection(
            hindi_keywords
        )

        has_hindi_words = (
            len(matched_words) > 0
        )

        if (
            has_devanagari
            or has_hindi_words
        ):

            logger.info(
                "Detected Hindi/Hinglish speech: %s | Matched: %s",
                transcript,
                matched_words,
            )

            session.tts.update_options(
                voice="hi-IN-anisha"
            )

        else:

            logger.info(
                "Detected English speech: %s",
                transcript,
            )

            session.tts.update_options(
                voice="en-IN-anisha"
            )

    # -------------------------------------------------
    # CONNECT TO LIVEKIT ROOM
    # -------------------------------------------------

    await ctx.connect()

    # -------------------------------------------------
    # START AGENT SESSION
    # -------------------------------------------------

    await session.start(

        agent=Assistant(),

        room=ctx.room,

        room_options=room_io.RoomOptions(

            audio_input=room_io.AudioInputOptions(

                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if (
                        params.participant.kind
                        == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    )
                    else noise_cancellation.BVC()
                ),

            ),

        ),

    )

    # -------------------------------------------------
    # OUTBOUND AI GREETING
    # -------------------------------------------------

    if is_outbound:

        user_name = outbound_metadata.get(
            "user_name",
            "friend"
        )

        scheme_name = outbound_metadata.get(
            "scheme_name",
            "your financial scheme"
        )

        deadline = outbound_metadata.get(
            "deadline",
            "the upcoming deadline"
        )

        logger.info(
            "Starting outbound FinSaathi greeting "
            "for %s",
            user_name,
        )

        await session.generate_reply(
            instructions=(
                f"Start the outbound reminder call now. "
                f"Do not wait for the user to speak first. "
                f"Briefly greet {user_name} by name. "
                f"Introduce yourself as FinSaathi AI. "
                f"Explain that you are calling because "
                f"they were previously found eligible for "
                f"{scheme_name}. "
                f"Tell them that the application deadline "
                f"is {deadline}. "
                f"Keep the opening natural and concise. "
                f"Tell them they can say stop if they do "
                f"not want future reminder calls. "
                f"Then ask if they want help with the scheme."
            )
        )


if __name__ == "__main__":

    cli.run_app(server)
