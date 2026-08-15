# FinSaathi AI — Voice Agent for Financial Services

**FinSaathi AI** is a multilingual, voice-first financial services assistant built for the **Murf AI — 10 Days of Voice Agents: VoiceForBharat Edition 2026**.

It combines real-time voice communication, AI reasoning, tool calling, caller memory, government-scheme workflows, outbound reminders, human-support escalation, analytics, and specialist-agent routing into one conversational system.

> **Safety:** FinSaathi provides general information and guidance. It is not a bank employee, government officer, or financial advisor, and it does not guarantee approvals or financial outcomes.

---

## 🚀 What is FinSaathi?

FinSaathi is designed to make financial-service workflows easier to access through natural voice conversations.

Users can communicate in **English, Hindi, or Hinglish** instead of navigating complicated forms or searching through multiple websites.

For example:

> **User:** "PMJJBY ke liye main eligible hoon?"

Instead of simply returning a webpage, FinSaathi can understand the request, collect the required information, run the eligibility workflow, and explain the result conversationally.

The system can also identify situations where human assistance is more appropriate and create a support request after user confirmation.

---

# ✨ Features

- 🎙️ Real-time voice conversations.
- 🇮🇳 English, Hindi, and Hinglish support.
- 🧠 Google Gemini powered reasoning.
- 🎧 Deepgram Speech-to-Text.
- 🔊 Murf Falcon Text-to-Speech.
- ⚡ LiveKit real-time voice transport.
- 🏛️ Government-scheme information.
- ✅ Scheme eligibility checking.
- 📄 Document and application guidance.
- 🧠 Persistent caller profiles and memory.
- 📞 Outbound calls and reminders.
- 🤝 Human-support escalation.
- 📊 Call outcome analytics.
- 🔀 Specialist-agent handoffs.
- 🔐 Safety guardrails for sensitive financial information.
- 🖥️ Human-support management dashboard.

---

# 🗓️ 10 Days of Voice Agents — Development Journey

The project was developed progressively over 10 days, with each day adding another important capability to the voice-agent system.

## Day 1 — Core Voice Agent 🎙️

The project started with the basic real-time voice-agent pipeline.

The first objective was to create an agent that could listen to a user, understand speech, generate a response, and speak back naturally.

### Core pipeline

```text
User
  ↓
LiveKit
  ↓
Speech-to-Text
  ↓
LLM
  ↓
Text-to-Speech
  ↓
LiveKit
  ↓
User
```

The initial implementation established the foundation for all later features.

### Technologies introduced

- LiveKit Agents
- Deepgram STT
- Google Gemini
- Murf TTS

---

## Day 2 — Agent Personality & Guardrails 🧠

The next step was defining how FinSaathi should behave.

The agent was given clear instructions instead of behaving like a generic chatbot.

The system instructions focused on:

- Helpful and conversational responses.
- Clear explanations.
- Hindi, English, and Hinglish conversations.
- Asking for required information before workflows.
- Avoiding unsupported claims.
- Knowing when to escalate to human support.
- Protecting sensitive financial information.

The agent was explicitly instructed not to request sensitive credentials such as:

- OTPs.
- PINs.
- Passwords.
- CVVs.
- Full card details.
- Full bank-account numbers.
- Government ID numbers.

This established the safety foundation for the rest of the project.

---

## Day 3 — Indian Language & Code-Mixed Conversations 🇮🇳

The voice experience was adapted for Indian users.

FinSaathi was designed to understand:

- English.
- Hindi.
- Hinglish.
- Code-mixed conversations.

For example:

```text
"PMJJBY ke liye main eligible hoon?"
```

or:

```text
"Mujhe scheme ke documents bata do."
```

The goal was to make the interaction feel like a natural conversation rather than a traditional form-based financial application.

---

## Day 4 — Voice Interface & Conversation Experience 🖥️

The next stage focused on connecting the voice agent to the application interface.

The application was structured around a continuous conversation:

```text
Connect
  ↓
Speak
  ↓
Agent listens
  ↓
Agent reasons
  ↓
Agent responds
  ↓
Continue conversation
```

LiveKit maintains the real-time communication layer while the AI agent handles the conversation and workflow logic.

---

## Day 5 — Government Scheme Eligibility 🏛️

FinSaathi was extended from a conversational assistant into a task-oriented agent.

Government-scheme workflows were introduced for:

- **PMMY** — Pradhan Mantri Mudra Yojana
- **PMJJBY** — Pradhan Mantri Jeevan Jyoti Bima Yojana
- **PMSBY** — Pradhan Mantri Suraksha Bima Yojana

Scheme information is maintained in:

```text
backend/data/financial_schemes.json
```

The `check_scheme_eligibility` tool collects the required information and evaluates it against the configured scheme rules.

### Eligibility flow

```text
User asks about scheme
        ↓
Agent identifies scheme
        ↓
Collect required information
        ↓
check_scheme_eligibility()
        ↓
Scheme rules
        ↓
Eligibility result
        ↓
Agent explains result
```

This was the point where FinSaathi started behaving more like an agent instead of a simple voice chatbot.

---

## Day 6 — Caller Memory & Outbound Calls 🧠📞

Persistent caller information was added using SQLite.

Database:

```text
backend/data/users.db
```

The database stores structured caller information, consent, eligibility state, and outbound-call state.

### Caller memory

```text
User
 ↓
Conversation
 ↓
Relevant Information
 ↓
SQLite
 ↓
Future Conversation
 ↓
Stored Context
```

Outbound reminder functionality was also introduced.

Implementation:

```text
backend/src/outbound_call.py
```

This allowed FinSaathi to support workflows where the system could initiate a call instead of only responding to incoming conversations.

---

## Day 7 — Human Support Escalation 🤝

FinSaathi can identify situations where human support is more appropriate.

Examples include:

- Possible unauthorized or fraudulent transactions.
- Requests outside the agent's scope.
- Explicit requests for human assistance.

### Escalation workflow

```text
User issue
    ↓
AI identifies human-support need
    ↓
AI explains why
    ↓
AI asks for permission
    ↓
User confirms
    ↓
create_escalation()
    ↓
SQLite
    ↓
Reference ID generated
    ↓
Human Support Dashboard
```

Example reference ID:

```text
FS-A5323F
```

Escalation records can contain:

- Request ID.
- User ID.
- Reason.
- Short summary.
- What the AI checked.
- Urgency.
- Language.
- Preferred follow-up.
- Status.
- Creation time.
- Resolution.
- Resolved time.

Sensitive credentials are never intended to be stored in escalation summaries.

---

## Day 8 — Call Analytics 📊

Once FinSaathi started handling real workflows, call outcomes became important.

Call analytics were added to track what happened during conversations.

### Analytics flow

```text
Voice Conversation
       ↓
Call Outcome
       ↓
Database
       ↓
Analytics API
       ↓
Dashboard
```

This provides visibility into conversation outcomes and helps evaluate how successfully different workflows are completed.

---

## Day 9 — Specialist Agent Handoff 🔀

As more workflows were added, it became important not to put every responsibility inside one large agent.

FinSaathi was extended with specialist-agent routing.

### Example

```text
User
  ↓
FinSaathi Main Agent
  ↓
Detect Intent
  ↓
Specialist Agent
  ↓
Specialized Workflow
  ↓
Result
  ↓
User
```

For example, a government-scheme request can be routed to a specialist workflow responsible for scheme information and eligibility.

Relevant conversation context can be passed to the specialist so the user does not need to repeat the entire conversation.

---

## Day 10 — Complete Voice Agent System 🚀

By Day 10, the individual capabilities were combined into one complete voice-agent system.

FinSaathi could combine:

```text
Real-Time Voice
      +
Multilingual Conversations
      +
LLM Reasoning
      +
Tools
      +
Memory
      +
Eligibility Workflows
      +
Outbound Calls
      +
Human Escalation
      +
Call Analytics
      +
Specialist Agents
```

The final system moved from a basic voice assistant toward a complete agentic financial-assistance platform.

---

# 🏗️ Architecture

## Complete System Architecture

```text
                         ┌───────────────────┐
                         │       User        │
                         └─────────┬─────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │      LiveKit      │
                         │  Real-time Voice  │
                         └─────────┬─────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │    Deepgram STT   │
                         └─────────┬─────────┘
                                   │
                                   ▼
                         ┌───────────────────┐
                         │   Google Gemini   │
                         │   Main Agent      │
                         └─────────┬─────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
        ┌─────────────┐     ┌─────────────┐     ┌──────────────┐
        │    Tools    │     │ Specialist  │     │   Human      │
        │             │     │   Agents    │     │ Escalation   │
        └──────┬──────┘     └─────────────┘     └──────┬───────┘
               │                                        │
               ▼                                        ▼
    ┌────────────────────┐                       ┌─────────────┐
    │ Scheme / Workflow  │                       │   SQLite    │
    │      Logic         │                       │  users.db   │
    └─────────┬──────────┘                       └──────┬──────┘
              │                                         │
              ▼                                         ▼
    financial_schemes.json                         FastAPI
                                                        │
                                                        ▼
                                                 Next.js Dashboard


                    Normal Agent Response
                             │
                             ▼
                    ┌─────────────────┐
                    │   Murf Falcon   │
                    │      TTS        │
                    └────────┬────────┘
                             │
                             ▼
                          LiveKit
                             │
                             ▼
                            User
```

---

# 🧩 Technology Stack

| Layer | Technology |
|---|---|
| Real-time Voice | LiveKit Agents |
| Speech-to-Text | Deepgram |
| LLM | Google Gemini |
| Text-to-Speech | Murf Falcon |
| Backend | Python |
| Database | SQLite |
| API | FastAPI |
| Frontend | Next.js |
| Package Manager | uv / pnpm |
| Scheme Data | JSON |
| Voice Transport | LiveKit |

---

# 📁 Project Structure

```text
murf-livekit-starter/
│
├── backend/
│   ├── data/
│   │   ├── financial_schemes.json
│   │   └── users.db
│   │
│   ├── src/
│   │   ├── agent.py
│   │   ├── database.py
│   │   ├── escalation_api.py
│   │   ├── outbound_call.py
│   │   └── prompt.py
│   │
│   ├── tests/
│   ├── .env.example
│   ├── pyproject.toml
│   └── railway.toml
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx
│   │   ├── escalations/
│   │   │   └── page.tsx
│   │   └── api/token/
│   │
│   ├── components/
│   ├── app-config.ts
│   ├── .env.example
│   └── package.json
│
├── start_app.sh
├── start_app.ps1
└── README.md
```

---

# 🛠️ Important Files

| File | Purpose |
|---|---|
| `backend/src/agent.py` | Main LiveKit voice agent, STT, LLM, TTS and tools |
| `backend/src/database.py` | SQLite persistence layer |
| `backend/src/outbound_call.py` | Outbound calling/reminder logic |
| `backend/src/escalation_api.py` | Human-support API |
| `frontend/app/page.tsx` | Main FinSaathi interface |
| `frontend/app/escalations/page.tsx` | Human-support dashboard |
| `backend/data/financial_schemes.json` | Scheme eligibility data |
| `backend/data/users.db` | Caller and workflow data |

---

# ⚙️ Getting Started

## Prerequisites

- Python 3.10+
- Node.js 18+
- `uv`
- `pnpm`
- LiveKit Cloud project
- Murf API key
- Deepgram API key
- Google Gemini API key

## Backend Setup

```bash
cd backend
uv sync
uv run python src/agent.py download-files
```

## Frontend Setup

```bash
cd frontend
pnpm install
```

---

# 🔐 Environment Variables

Create your environment files using the provided `.env.example` files.

```env
LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

MURF_API_KEY=your_murf_api_key

DEEPGRAM_API_KEY=your_deepgram_api_key

GOOGLE_API_KEY=your_google_api_key
```

**Never commit real API keys, API secrets, caller information, or private database files to GitHub.**

---

# ▶️ Running Locally

## 1. Start the LiveKit Agent

From `backend`:

```bash
uv run python src/agent.py dev
```

## 2. Start Human Support API

From another backend terminal:

```bash
uv run uvicorn src.escalation_api:app --reload --port 8000
```

Health check:

```text
http://127.0.0.1:8000/api/health
```

Escalations API:

```text
http://127.0.0.1:8000/api/escalations
```

## 3. Start Frontend

From `frontend`:

```bash
pnpm dev
```

Main application:

```text
http://localhost:3000
```

Human Support Dashboard:

```text
http://localhost:3000/escalations
```

---

# 🧪 Example Conversations

### Financial Query

```text
User:
"PMMY kya hai?"

FinSaathi:
Explains the scheme and provides relevant information.
```

### Eligibility

```text
User:
"PMJJBY ke liye main eligible hoon?"

FinSaathi:
Collects the required information,
runs the eligibility workflow,
and explains the result.
```

### Human Escalation

```text
User:
"Mere account se unauthorized transaction hua hai."

FinSaathi:
Explains why human support may be required,
asks for confirmation,
creates an escalation,
and returns a reference ID.
```

---

# 🤝 Human Support Workflow

```text
OPEN
  ↓
Take Request
  ↓
IN_PROGRESS
  ↓
Resolve Request
  ↓
RESOLVED
```

The dashboard allows support staff to view and update escalation requests.

---

# 📡 API Reference

### Get all escalations

```http
GET /api/escalations
```

### Filter escalations

```http
GET /api/escalations?status=OPEN
```

### Get one escalation

```http
GET /api/escalations/FS-A5323F
```

### Update escalation

```http
PATCH /api/escalations/FS-A5323F
Content-Type: application/json
```

Example:

```json
{
  "status": "IN_PROGRESS",
  "resolution": null
}
```

Resolve:

```json
{
  "status": "RESOLVED",
  "resolution": "User was advised to contact the bank's official support channel."
}
```

---

# 🔒 Security & Privacy

FinSaathi is designed with financial-safety guardrails.

The agent should never request or store:

- OTPs.
- PINs.
- CVVs.
- Passwords.
- Full card numbers.
- Full bank-account numbers.
- Government ID numbers.

The agent should also never pretend to have access to systems that it does not actually access.

For sensitive or account-specific issues, FinSaathi provides guidance and can route the user toward human support or appropriate official channels.

For production deployment, additional controls should include:

- Authentication.
- Authorization.
- Secure secret management.
- Encrypted storage.
- Audit logging.
- Appropriate privacy and compliance controls.

---

# 📞 Outbound Calling

Outbound functionality is handled separately from the main voice-agent process.

```text
Reminder / User State
        ↓
outbound_call.py
        ↓
Call Initiation
        ↓
Voice Agent
        ↓
Conversation
        ↓
Call Outcome
```

Implementation:

```text
backend/src/outbound_call.py
```

---

# 📊 Call Analytics

Call outcomes are recorded so conversations can be evaluated after completion.

```text
Voice Conversation
        ↓
Call Outcome
        ↓
Database
        ↓
Analytics API
        ↓
Dashboard
```

This provides visibility into the success and outcome of agent workflows.

---

# 🔀 Specialist Agents

Specialist-agent routing allows FinSaathi to delegate domain-specific workflows.

```text
User
  ↓
Main FinSaathi Agent
  ↓
Intent Detection
  ↓
Specialist Agent
  ↓
Specialized Tools
  ↓
Result
  ↓
User
```

This keeps the main agent focused on conversation orchestration while specialized agents handle domain-specific workflows.

---

# 🧠 Agent Tool Architecture

A simplified tool can look like:

```python
@function_tool
async def check_scheme_eligibility(
    scheme: str,
    user_information: dict
):
    result = perform_eligibility_check(
        scheme,
        user_information
    )

    return result
```

The LLM determines **when** a tool should be used, while the actual business logic remains inside the tool.

This separation makes workflows easier to test, maintain, and extend.

---

# 🤝 Human Escalation Tool

A simplified escalation tool can look like:

```python
@function_tool
async def create_escalation(
    reason: str,
    summary: str,
    urgency: str = "normal",
    preferred_followup: str = "phone"
):
    request_id = create_escalation_record(
        reason=reason,
        summary=summary,
        urgency=urgency,
        preferred_followup=preferred_followup
    )

    return request_id
```

The user confirms before the escalation request is created.

---

# 🧠 What I Learned

Building FinSaathi taught me that a reliable voice agent is much more than:

```text
Speech-to-Text + LLM + Text-to-Speech
```

A production-style voice agent also needs:

- Prompt engineering.
- Tool integration.
- Memory.
- State management.
- Safety guardrails.
- Real-time communication.
- Human escalation.
- Analytics.
- Specialist-agent routing.
- Clear failure handling.

The biggest architectural shift was moving from:

```text
Question → Answer
```

to:

```text
Understand
    ↓
Decide
    ↓
Act
    ↓
Respond
```

That shift is what turns a basic voice chatbot into an actual **agentic system**.

---

# 🎯 Project Outcome

At the end of the 10-day challenge, FinSaathi evolved into a complete voice-first financial assistance system combining:

```text
Real-Time Voice
        +
Multilingual Conversations
        +
LLM Reasoning
        +
Tool Calling
        +
Memory
        +
Scheme Eligibility
        +
Outbound Calls
        +
Human Escalation
        +
Call Analytics
        +
Specialist Agents
```

The project demonstrates how multiple AI and backend components can work together to create a practical conversational application for Indian users.

---

# 🔗 Blog

I documented the complete 10-day journey, architecture, implementation details, challenges, and learnings in the blog:

**[Read the full FinSaathi build journey](https://dev.to/nipun_goel_720eefc9d5f127/building-finsaathi-a-voice-first-financial-assistant-for-bharat-5179)**

---

# 🧰 Tech Stack

### AI / Voice

- Google Gemini
- Deepgram
- Murf Falcon
- LiveKit Agents

### Backend

- Python
- FastAPI
- SQLite

### Frontend

- Next.js

### Data

- JSON
- SQLite

---

# 🏆 Challenge

Built as part of:

**Murf AI — 10 Days of Voice Agents: VoiceForBharat Edition 2026**

The project was developed progressively over 10 days, starting from a basic real-time voice agent and evolving into a system with tools, memory, outbound calling, human escalation, analytics, and specialist-agent workflows.

---

# 📄 License

MIT
