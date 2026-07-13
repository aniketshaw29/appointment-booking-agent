# Technical Reference

A walkthrough of each module, its responsibilities, and the key design decisions.

---

## Module Map

```
app.py                  ← Flask entry point, routes, admin panel
config.py               ← Env var loading and validation
errors.py               ← Custom exceptions + user-facing message strings
│
agent/
├── llm.py              ← Unified LLM router (Gemini + OpenAI)
├── prompts.py          ← System prompt injected into every LLM session
└── schemas.py          ← Pydantic model for structured LLM output
│
calendar_service/
├── google_cal.py       ← Google Calendar API wrapper (freebusy + create event)
└── db.py               ← SQLite: init, sessions, bookings
│
telephony/
└── telegram_sender.py  ← send_message(chat_id, text) → Telegram API
│
templates/
├── index.html          ← Landing page with 5s auto-redirect to Telegram bot
├── admin.html          ← Admin dashboard: model switcher
└── admin_login.html    ← Admin login page
│
tests/
└── test_app.py         ← 36 unit + integration tests
```

---

## `app.py` — Entry Point

**Responsibilities:**
- Registers all Flask routes
- Validates Telegram webhook signature on every `POST /webhook`
- Orchestrates the per-message flow: session load → LLM turn → calendar action → session save → reply
- Hosts the admin panel (`/admin`, `/admin/login`, `/admin/logout`, `/admin/set-model`)
- Maintains `_active_model` as a module-level variable (runtime model state)

**Key design decision — runtime model switching without a DB:**
`_active_model` is a simple Python module variable. Switching models via `/admin/set-model` just reassigns it. No DB write, no file write — instant. The downside is it resets on restart (which is intentional — `ACTIVE_MODEL` env var is the persistent default).

**Admin authentication:**
Uses Flask's built-in server-side session (`session["admin_logged_in"]`). The session key is `ADMIN_PASSWORD` itself — this means changing the password automatically invalidates all existing sessions.

---

## `agent/llm.py` — LLM Router

**Responsibilities:**
- Routes `process_turn(chat_id, text, model_id)` to the correct provider
- Maintains separate in-memory chat history for each provider:
  - Gemini: `genai.ChatSession` per `chat_id` (Gemini handles history internally)
  - OpenAI: `list[dict]` of messages per `chat_id` (we manage history manually)
- Parses LLM response into `AgentResponse` Pydantic model
- Raises typed exceptions: `GeminiQuotaError`, `GeminiError`

**Why separate history per provider?**
When you switch models mid-conversation via admin, the new model starts a fresh session (no shared history across providers). This is intentional — mixing Gemini and OpenAI history formats would be complex and the conversation context is short enough that starting fresh is fine.

**Response parsing:**
Both providers are told to return JSON. The parser strips markdown code fences (Gemini sometimes wraps JSON in ` ```json ``` `), then validates against `AgentResponse`. If parsing fails, it returns a `clarify` response asking the user to rephrase — never crashes.

---

## `agent/schemas.py` — Structured Output

Every LLM response must conform to `AgentResponse`:

```python
class AgentResponse(BaseModel):
    reply_text: str               # What the bot says to the user
    action: Literal["clarify", "check_availability", "book", "done"]
    extracted_name: str | None
    extracted_age: str | None
    extracted_location: str | None
    extracted_nature: str | None  # work | business | casual | other
    extracted_purpose: str | None
    proposed_slot: str | None     # ISO8601 datetime
```

**Why Pydantic?** Pydantic validates at parse time and raises a clear `ValidationError` if the LLM returns an invalid `action`. This prevents silent bugs where an unexpected action value would pass undetected.

---

## `agent/prompts.py` — System Prompt

The system prompt instructs the LLM to:
1. Collect all 5 fields conversationally (name → age → location → nature → purpose → datetime)
2. Always respond in the exact JSON format of `AgentResponse`
3. Parse relative dates ("next Monday", "tomorrow at 3") to absolute ISO8601 using today's date
4. Keep replies to 1-2 sentences

The prompt uses `{config.BUSINESS_NAME}` and `{config.BUSINESS_HOURS}` via f-string interpolation so it reflects the actual business settings.

---

## `calendar_service/google_cal.py` — Calendar

**Responsibilities:**
- `check_availability(slot_iso)` → `True` (free) / `False` (busy) — uses Google's freebusy API
- `create_event(...)` → creates a calendar event, returns Google event ID
- `next_available_slot(from_iso)` → walks hour-by-hour to find the next free slot within 7 days
- `_validate_slot(slot_iso)` → raises `BookingConflictError` if the slot is in the past

**Authentication:**
Uses a Google service account (not OAuth). The service account JSON is loaded from `GOOGLE_SERVICE_ACCOUNT_FILE`. On Render, this is placed at `/etc/secrets/service_account.json` via Render's Secret Files feature.

**Why service account vs OAuth?**
OAuth requires a browser-based consent flow and token refresh management. A service account is simpler for a server-side app that only accesses one calendar — you just share the calendar with the service account's email address.

---

## `calendar_service/db.py` — Database

See [DATABASE.md](DATABASE.md) for the full schema and query reference.

---

## `errors.py` — Error Handling

**Custom exception hierarchy:**
```
Exception
├── GeminiError
│   └── GeminiQuotaError        (429 ResourceExhausted)
├── CalendarError
│   └── CalendarAuthError       (missing/invalid service account)
└── BookingConflictError        (slot in past, duplicate booking)
```

**User-facing messages:**
All user-visible error messages live in `MESSAGES` dict. This keeps UI copy out of the business logic and makes it easy to change wording without touching the core code.

**`log_error(context, exc)`:**
Logs the full traceback to server logs (visible in Render's log panel) without exposing it to the user. This is the only place `traceback.format_exc()` is called.

---

## `telephony/telegram_sender.py`

A thin wrapper around `requests.post` to Telegram's `sendMessage` API. Kept as a separate module so it can be mocked in tests and later replaced with a Twilio TTS response without touching `app.py`.

---

## `templates/index.html` — Landing Page

Static HTML + inline CSS (no external dependencies). Features:
- 5-second auto-redirect countdown to `t.me/aniketshaw_appointment_bot`
- Cancel button stops the countdown
- "How it works" 3-step section
- Business hours card
- All content injected by Flask via Jinja2 (`{{ business_name }}`, `{{ business_hours }}`)

---

## `templates/admin.html` — Admin Dashboard

Password-protected. Features:
- Current active model and OpenAI key status
- Model cards with radio buttons — one click to switch
- Locked state (greyed out) for GPT models when `OPENAI_API_KEY` is not set
- Jinja2 conditional rendering for lock state and badges

---

## Design Decisions

| Decision | Rationale |
|---|---|
| SQLite over Postgres | Zero-ops for a personal project; trivial to switch later |
| Flask over FastAPI | Webhooks are synchronous request/response; async gives no benefit |
| Module-level `_active_model` | Simplest runtime toggle without a DB; resets on restart by design |
| Gemini `ChatSession` per user | Gemini handles conversation history internally; no manual history management needed |
| OpenAI manual history | OpenAI stateless API requires client-side history management |
| Pydantic for LLM output | Validates JSON structure at parse time; prevents silent action mismatches |
| Service account over OAuth | Single-calendar, server-side app; no consent flow needed |
| Typed exceptions | Specific error messages per failure type instead of generic "something went wrong" |
| `INSERT OR IGNORE` on bookings | Idempotent — Telegram retries webhooks; second insert is a no-op |
