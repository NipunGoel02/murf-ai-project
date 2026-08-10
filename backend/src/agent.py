import asyncio
import json
import logging
import re
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
    data_file = Path(__file__).resolve().parent.parent / "data" / "financial_schemes.json"
    try:
        with open(data_file, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except FileNotFoundError as exc:
        raise FileNotFoundError("Financial schemes dataset not found.") from exc
    except json.JSONDecodeError as exc:
        raise ValueError("Financial schemes dataset is not valid JSON.") from exc

    schemes = {}
    for scheme in raw.get("schemes", []):
        scheme_id = str(scheme.get("scheme_id", "")).strip().upper()
        if scheme_id:
            schemes[scheme_id] = scheme
    return schemes


def _normalize_scheme_name(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.strip().lower())


def _find_scheme(scheme_name: str, schemes: dict[str, dict]) -> dict | None:
    normalized_query = _normalize_scheme_name(scheme_name)
    if not normalized_query:
        return None

    for scheme_id, scheme in schemes.items():
        normalized_id = _normalize_scheme_name(scheme_id)
        normalized_name = _normalize_scheme_name(scheme.get("name", ""))

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
        super().__init__(instructions=SYSTEM_PROMPT)
        init_db()

    @staticmethod
    def _caller_user_id(context: RunContext) -> str | None:
        """Resolve the caller's identity.

        Uses the session's RoomIO linked participant (the human caller).
        Returns None if no caller is found.
        """
        room_io = None
        try:
            room_io = getattr(context.session, "room_io", None)
            if room_io is not None:
                participant = getattr(room_io, "linked_participant", None)
                if participant is not None:
                    return participant.identity
        except Exception:
            pass
        # Fallback: scan the room participants for a non-agent participant.
        try:
            room = getattr(room_io, "room", None)
            if room is None:
                room = getattr(context, "room", None)
            if room is not None:
                for participant in room.participants.values():
                    if participant.kind != rtc.ParticipantKind.PARTICIPANT_KIND_AGENT:
                        return participant.identity
                for participant in room.remote_participants.values():
                    return participant.identity
        except Exception:
            pass
        return None

    @function_tool
    async def lookup_user(self, context: RunContext) -> dict | None:
        """Look up a caller's saved profile.

        Returns the caller's name, language preference, and any facts saved
        from previous conversations, or None if the caller is new.

        Call this at the start of every conversation to check whether the
        caller is returning. If a profile is returned, greet the caller by
        name and continue from where you last left off.
        """
        user_id = self._caller_user_id(context)
        profile = find_user(user_id)
        logger.info("lookup_user(%s) -> %s", user_id, profile)
        return profile

    @function_tool
    async def save_user(
        self,
        context: RunContext,
        name: str,
        facts: str,
        language_preference: str | None = None,
    ) -> str:
        """Save or update a caller's profile.

        Only call this AFTER the caller has explicitly agreed to be remembered.
        Never store account numbers, card numbers, OTPs, PINs, or government
        ID numbers. Store only structured facts (e.g. schemes already checked,
        eligibility answers).

        Args:
            name: The caller's name.
            facts: A JSON object of facts about the caller (key/value pairs).
            language_preference: The language the caller prefers
                (e.g. "hindi", "english", "hinglish").
        """
        user_id = self._caller_user_id(context)
        if not user_id:
            return "I could not identify the caller, so I did not save anything."
        try:
            facts_dict = json.loads(facts) if facts else {}
        except json.JSONDecodeError:
            facts_dict = {}
        existing = find_user(user_id)
        if existing is None:
            save_user(user_id, name, language_preference, facts_dict)
        else:
            if name:
                save_user(user_id, name, language_preference, existing["facts"])
            if facts_dict:
                update_facts(user_id, facts_dict)
        logger.info("save_user(%s, %s, %s)", user_id, name, facts_dict)
        return f"Saved profile for {name}."

    @function_tool
    async def check_scheme_eligibility(
        self,
        scheme_name: str,
        citizenship: str,
        age: int,
        has_savings_bank_account: bool | None = None,
        auto_debit_available: bool | None = None,
        business_purpose: str | None = None,
    ) -> dict:
        """Use this tool when the user asks whether they may be eligible for a
        supported government financial scheme and the required eligibility
        information has already been collected.

        Do not use this tool for general financial questions, investment advice,
        banking transactions, OTPs, PINs, passwords, account-specific requests,
        or financial credentials.

        The result is an eligibility indication based on the stored scheme
        criteria. It is not an official approval or guarantee.
        """
        try:
            schemes = _load_financial_schemes()
        except Exception as exc:
            logger.error("Scheme eligibility tool failed loading dataset: %s", exc)
            return {
                "success": False,
                "error": "Dataset unavailable. Please try again later or check the official Government of India source.",
            }

        scheme = _find_scheme(scheme_name, schemes)
        if scheme is None:
            logger.info("Unsupported scheme requested: %s", scheme_name)
            return {
                "success": False,
                "error": "Unsupported scheme. Supported schemes are PMMY, PMJJBY, and PMSBY.",
            }

        scheme_id = scheme["scheme_id"].upper()
        required_missing = []
        if scheme_id == "PMMY" and not business_purpose:
            required_missing.append("business_purpose")
        if scheme_id in {"PMJJBY", "PMSBY"}:
            if has_savings_bank_account is None:
                required_missing.append("has_savings_bank_account")
            if auto_debit_available is None:
                required_missing.append("auto_debit_available")

        if required_missing:
            logger.info(
                "Scheme eligibility tool missing required inputs: %s for %s",
                required_missing,
                scheme_id,
            )
            return {
                "success": False,
                "error": "Missing required eligibility information. Please provide the missing details before checking the scheme.",
            }

        normalized_citizenship = citizenship.strip().lower() if citizenship else ""
        is_indian_citizen = any(
            token in normalized_citizenship
            for token in ["indian", "hindustan", "bharatiya", "haan", "yes", "y", "true"]
        )

        failures = []
        if not is_indian_citizen:
            failures.append("The applicant does not appear to be an Indian citizen.")

        minimum_age = scheme["eligibility"].get("minimum_age")
        maximum_age = scheme["eligibility"].get("maximum_age")
        if minimum_age is not None and age < minimum_age:
            failures.append(
                f"The applicant must be at least {minimum_age} years old."
            )
        if maximum_age is not None and age > maximum_age:
            failures.append(
                f"The applicant must be no older than {maximum_age} years old."
            )

        if scheme_id in {"PMJJBY", "PMSBY"}:
            if not has_savings_bank_account:
                failures.append(
                    "A valid savings bank account with auto-debit capability is required."
                )
            if not auto_debit_available:
                failures.append(
                    "Auto-debit authorization from the savings bank account is required."
                )

        if scheme_id == "PMMY":
            normalized_purpose = business_purpose.strip().lower() if business_purpose else ""
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
            if not any(keyword in normalized_purpose for keyword in business_indicators):
                failures.append(
                    "The scheme is for business purposes or non-farm enterprise activities only."
                )

        eligible = len(failures) == 0
        result = {
            "success": True,
            "scheme_id": scheme_id,
            "scheme_name": scheme["name"],
            "eligible": eligible,
            "reasons": failures if failures else ["The provided information satisfies the listed eligibility criteria."],
            "checked_criteria": {
                "citizenship": citizenship,
                "age": age,
                "has_savings_bank_account": has_savings_bank_account,
                "auto_debit_available": auto_debit_available,
                "business_purpose": business_purpose,
            },
            "source": scheme.get("source"),
            "source_url": scheme.get("source_url"),
            "last_verified": scheme.get("last_verified"),
        }

        logger.info(
            "Scheme eligibility check completed for %s: eligible=%s",
            scheme_id,
            eligible,
        )
        return result


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3", language="multi"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
                model="gemini-3.5-flash-lite",
            ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # See all available models as well as voice selections at https://docs.livekit.io/agents/models/tts/
        tts=murf.TTS(
                voice="hi-IN-anisha",
                style="Conversation",
                tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
                text_pacing=True
            ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    @session.on("user_input_transcribed")
    def on_user_input_transcribed(ev: UserInputTranscribedEvent):
        asyncio.create_task(handle_user_input_transcribed(ev))

    async def handle_user_input_transcribed(ev: UserInputTranscribedEvent):
        transcript = ev.text.strip().lower()

        if not transcript:
            return

        # Check for Devanagari (Native Hindi)
        has_devanagari = any(
            '\u0900' <= ch <= '\u097F'
            for ch in transcript
        )

        # Common Hindi / Hinglish keywords
        hindi_keywords = {

            # Greetings
            "namaste", "namaskar", "helloji", "ramram", "pranam",

            # Pronouns
            "main", "mai", "mein", "me", "mera", "meri", "mere",
            "mujhe", "mujhko", "hum", "ham", "hamara", "hamari",
            "aap", "ap", "tum", "tumhara", "tumhari", "tumhe",
            "bhai", "behen", "sir", "madam", "ji",

            # Common words
            "hai", "hu", "ho", "tha", "thi", "the", "hoga", "hogi",
            "haan", "han", "ha", "nahi", "nahin", "na", "acha", "achha",
            "theek", "thik", "bilkul", "jarur", "zarur", "please",

            # Question words
            "kya", "kaise", "kab", "kahan", "kidhar", "kyu", "kyon",
            "kaun", "kis", "kitna", "kitni", "kitne", "kaunsa",

            # Time
            "aaj", "kal", "abhi", "subah", "dopahar", "shaam", "raat",
            "ab", "baad", "pehle", "phir",

            # Medical
            "doctor", "hospital", "clinic", "appointment",
            "bukhar", "fever", "dard", "pain", "khansi", "cough",
            "sardi", "cold", "gala", "pet", "sar", "headache",
            "ulti", "vomit", "chakkar", "injury", "emergency",
            "medicine", "dawai", "tablet", "checkup", "test",
            "blood", "sugar", "bp", "pressure", "oxygen",
            "breathing", "saans", "operation", "surgery",

            # Actions
            "karna", "karni", "karo", "kar", "book", "cancel",
            "reschedule", "milna", "jana", "aana", "dekhna",
            "batana", "sunna", "madad", "help", "chahiye",
            "hona", "bolna", "boliye", "bataye", "batana",

            # Relations
            "maa", "papa", "pitaji", "mataji", "beta", "beti", "uncle", "aunty", "dada", "dadi",
            "nana", "nani", "wife", "husband", "bacha", "baccha",

            # Misc
            "haanji", "jihaan", "shukriya", "dhanyawad",
            "kripya", "urgent", "jaldi"
        }

        # Split into words
        words = set(re.findall(r"[a-zA-Z\u0900-\u097F]+", transcript))

        # Count Hindi keywords
        matched_words = words.intersection(hindi_keywords)

        has_hindi_words = len(matched_words) > 0

        if has_devanagari or has_hindi_words:

            logger.info(
                f"Detected Hindi/Hinglish speech: {transcript} | Matched: {matched_words}"
            )

            session.tts.update_options(
                voice="hi-IN-anisha"
            )

        else:

            logger.info(
                f"Detected English speech: {transcript}"
            )

            session.tts.update_options(
                voice="en-IN-anisha"
            )

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(server)

