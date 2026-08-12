# FinSaathi AI --- Voice Agent for Financial Services

FinSaathi AI is a multilingual financial-services voice assistant built
for the **Murf AI Voice for Bharat Challenge 2026**.

It combines LiveKit Agents, Deepgram STT, Google Gemini, and Murf TTS
for conversational financial guidance, government-scheme eligibility
checks, deadline reminders, and human-support escalation.

> **Safety:** FinSaathi provides general information and guidance. It is
> not a bank employee, government officer, or financial advisor, and it
> does not guarantee approvals or financial outcomes.

## Features

### Core Voice Agent

-   English, Hindi, and Hinglish conversations
-   LiveKit real-time voice transport
-   Deepgram speech-to-text
-   Google Gemini LLM
-   Murf TTS
-   Automatic Hindi/Hinglish voice switching
-   Caller profile persistence through SQLite

### Day 5 --- Scheme Eligibility

The agent can check eligibility for: - **PMMY** --- Pradhan Mantri Mudra
Yojana - **PMJJBY** --- Pradhan Mantri Jeevan Jyoti Bima Yojana -
**PMSBY** --- Pradhan Mantri Suraksha Bima Yojana

Dataset:

``` text
backend/data/financial_schemes.json
```

The `check_scheme_eligibility` tool collects required information and
checks it against the local scheme rules.

### Day 6 --- Caller Profiles and Outbound Reminders

Caller information is stored in:

``` text
backend/data/users.db
```

The `users` table stores structured profile information, consent,
eligibility state, and outbound-call state.

Outbound reminder logic is handled separately by:

``` text
backend/src/outbound_call.py
```

### Day 7 --- Human Support Escalation

FinSaathi can escalate cases that require human support, including: -
Possible unauthorized/fraudulent transactions - Decisions or actions
outside the AI agent's scope - Explicit user requests for human support

The flow is:

``` text
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
SQLite users.db
        ↓
Reference ID generated
        ↓
Human Support Dashboard
```

Reference IDs are generated automatically, for example:

``` text
FS-A5323F
```

Escalations store: - request ID - user ID - reason - short summary -
what the AI checked - urgency - language - preferred follow-up -
status - creation time - resolution - resolved time

Sensitive information must never be stored in escalation summaries,
including OTPs, PINs, CVVs, passwords, full card numbers, full
bank-account numbers, or government ID numbers.

## Human Support Dashboard

The Day 7 dashboard is available at:

``` text
http://localhost:3000/escalations
```

It displays escalation requests and supports:

``` text
OPEN
  ↓
IN_PROGRESS
  ↓
RESOLVED
```

The dashboard includes reference ID, caller ID, reason, urgency,
preferred follow-up, AI summary, what the AI checked, and resolution
details.

## Architecture

### Voice / AI

``` text
User
  ↓
LiveKit
  ↓
Deepgram STT
  ↓
Google Gemini
  ├── Normal response → Murf TTS → LiveKit → User
  ├── check_scheme_eligibility() → financial_schemes.json
  └── create_escalation() → users.db
```

### Human-support dashboard

``` text
users.db
   ↓
database.py
   ↓
escalation_api.py
   ↓
FastAPI
   ↓
Next.js /escalations
```

`database.py` is a shared Python persistence module. It is not normally
run separately. The agent and other backend processes import its
functions directly. The browser dashboard uses FastAPI because the
browser should not access SQLite directly.

## Project Structure

``` text
murf-livekit-starter/
├── backend/
│   ├── data/
│   │   ├── financial_schemes.json
│   │   └── users.db
│   ├── src/
│   │   ├── agent.py
│   │   ├── database.py
│   │   ├── escalation_api.py
│   │   ├── outbound_call.py
│   │   └── prompt.py
│   ├── tests/
│   ├── .env.example
│   ├── pyproject.toml
│   └── railway.toml
├── frontend/
│   ├── app/
│   │   ├── page.tsx
│   │   ├── escalations/
│   │   │   └── page.tsx
│   │   └── api/token/
│   ├── components/
│   ├── app-config.ts
│   ├── .env.example
│   └── package.json
├── start_app.sh
├── start_app.ps1
└── README.md
```

## Quickstart

### Prerequisites

-   Python 3.10+
-   Node.js 18+
-   `uv`
-   `pnpm`
-   LiveKit Cloud project
-   Murf API key
-   Deepgram API key
-   Google Gemini API key

### Backend

``` bash
cd backend
uv sync
uv run python src/agent.py download-files
```

### Frontend

``` bash
cd frontend
pnpm install
```

## Run Locally

### 1. LiveKit Agent

From `backend`:

``` bash
uv run python src/agent.py dev
```

### 2. Human Support API

From another `backend` terminal:

``` bash
uv run uvicorn src.escalation_api:app --reload --port 8000
```

API:

``` text
http://127.0.0.1:8000
```

Health check:

``` text
http://127.0.0.1:8000/api/health
```

Escalations:

``` text
http://127.0.0.1:8000/api/escalations
```

### 3. Frontend

From `frontend`:

``` bash
pnpm dev
```

Main app:

``` text
http://localhost:3000
```

Human support:

``` text
http://localhost:3000/escalations
```

## Day 7 Testing

### Normal conversation

Test a normal request such as:

> "PMMY kya hai?"

The agent should answer normally and should not create an escalation.

### Escalation conversation

Test:

> "Mere account se ek unauthorized transaction hua hai."

The agent should explain why human support is appropriate and ask for
permission.

After the user confirms, the agent creates a request and returns a
reference ID such as:

``` text
FS-A5323F
```

### Verify the database

From `backend`:

``` bash
uv run python -c "from src.database import get_escalations; print(get_escalations())"
```

### Verify the dashboard

Open:

``` text
http://localhost:3000/escalations
```

The new request should appear as `OPEN`.

Then test:

``` text
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

### Reset demo/test escalations

To remove only escalation test records while preserving user profiles:

``` powershell
uv run python -c "import sqlite3; conn=sqlite3.connect('data/users.db'); conn.execute('DELETE FROM escalations'); conn.commit(); print('Escalations reset:', conn.execute('SELECT COUNT(*) FROM escalations').fetchone()[0]); conn.close()"
```

## API Reference

### Get all escalations

``` http
GET /api/escalations
```

Optional filter:

``` http
GET /api/escalations?status=OPEN
```

### Get one escalation

``` http
GET /api/escalations/FS-A5323F
```

### Update escalation

``` http
PATCH /api/escalations/FS-A5323F
Content-Type: application/json
```

Example:

``` json
{
  "status": "IN_PROGRESS",
  "resolution": null
}
```

Resolve example:

``` json
{
  "status": "RESOLVED",
  "resolution": "User was advised to contact the bank's official support channel."
}
```

## Important Files

  ---------------------------------------------------------------------------
  File                                    Purpose
  --------------------------------------- -----------------------------------
  `backend/src/agent.py`                  LiveKit agent, STT/LLM/TTS, tools,
                                          escalation logic

  `backend/src/database.py`               Shared SQLite persistence layer

  `backend/src/outbound_call.py`          Deadline/reminder outbound worker

  `backend/src/escalation_api.py`         FastAPI API for human-support
                                          dashboard

  `frontend/app/page.tsx`                 Existing main FinSaathi page

  `frontend/app/escalations/page.tsx`     Human-support dashboard

  `backend/data/financial_schemes.json`   Scheme eligibility dataset

  `backend/data/users.db`                 Local SQLite database
  ---------------------------------------------------------------------------

The existing main `frontend/app/page.tsx` and outbound architecture are
kept separate from the Day 7 dashboard.

## Security and Privacy

Never ask for or store: - OTPs - PINs - CVVs - Passwords - Full card
numbers - Full bank-account numbers - Government ID numbers

Production deployments should additionally use authentication,
authorization, secure secret management, encrypted storage, audit
logging, and appropriate privacy/compliance controls.

## Deployment Notes

The project contains multiple runtime components:

``` text
LiveKit Agent
    └── backend/src/agent.py

Outbound Worker
    └── backend/src/outbound_call.py

Human Support API
    └── backend/src/escalation_api.py

Next.js Frontend
    └── frontend/
```

For local development, these can run in separate terminals. In
production, deploy the agent, outbound worker, API, and frontend as
appropriately managed services. The frontend should use an environment
variable for the API base URL instead of a hard-coded localhost URL.

## Links

-   [Murf API Docs](https://murf.ai/api/docs)
-   [Murf Voice
    Library](https://murf.ai/api/docs/voices-styles/voice-library)
-   [LiveKit Docs](https://docs.livekit.io)
-   [Deepgram Docs](https://developers.deepgram.com)
-   [FastAPI](https://fastapi.tiangolo.com/)
-   [Next.js](https://nextjs.org/)
-   [uv](https://docs.astral.sh/uv/)
-   [pnpm](https://pnpm.io/)

## License

MIT
