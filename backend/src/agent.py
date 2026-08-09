import asyncio
import json
import logging
import re

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

