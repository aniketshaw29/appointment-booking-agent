# Appointment Booking Agent — Development Plan

## What We're Building

A Telegram bot that books appointments through a natural conversation. When someone messages the bot, the AI:
1. Greets the user and collects their name
2. Asks for their preferred appointment date and time
3. Checks availability against Google Calendar
4. Confirms the booking (or offers an alternative slot)
5. Saves the appointment to SQLite and creates a Google Calendar event

**Stack:** Python · Flask · Telegram Bot API · Google Gemini Flash · Google Calendar API · SQLite

**Future upgrade:** Swap Telegram for Twilio to make it a real phone calling agent (see [FUTURE_PHONE.md](FUTURE_PHONE.md))

---

## Project Structure

```
appointment-booking-agent/
├── app.py                        # Flask entry point, Telegram webhook handler
├── config.py                     # Env var loading (fails fast if missing)
├── requirements.txt
├── .env.example
├── .gitignore
│
├── agent/
│   ├── conversation.py           # ConversationManager — calls Gemini, tracks dialog history
│   ├── prompts.py                # System prompt + few-shot examples
│   └── schemas.py                # Pydantic models for Gemini's structured JSON output
│
├── calendar_service/
│   ├── google_cal.py             # Google Calendar API wrapper
│   └── db.py                    # SQLite: sessions + bookings tables
│
├── telephony/
│   └── telegram_sender.py       # Send messages back via Telegram Bot API
│
├── tests/
│   ├── test_conversation.py
│   ├── test_calendar.py
│   └── test_telegram.py
│
└── credentials/
    └── .gitkeep                  # Google service account JSON goes here (gitignored)
```

---

## Build Phases

### Phase 1 — Telegram Skeleton (Day 1)

**Goal:** Bot receives a message and replies.

- [ ] Create bot via @BotFather on Telegram → get `TELEGRAM_BOT_TOKEN`
- [ ] `config.py` — load and validate all env vars at startup
- [ ] `telephony/telegram_sender.py` — `send_message(chat_id, text)` helper
- [ ] `app.py` — `POST /webhook` receives Telegram updates, echoes back
- [ ] Set webhook URL via `ngrok` + Telegram Bot API
- [ ] Test: message the bot, it replies

### Phase 2 — Database Layer (Day 1–2)

**Goal:** Persist conversation sessions and bookings.

- [ ] `calendar_service/db.py`
  - `sessions` table: `chat_id`, `history JSON`, `state`, `name`, `proposed_slot`
  - `bookings` table: `id`, `name`, `telegram_user`, `datetime`, `google_event_id`, `status`
  - Functions: `get_or_create_session`, `save_session`, `create_booking`, `get_bookings_in_range`

### Phase 3 — Gemini Conversation Engine (Day 2–3)

**Goal:** AI drives the booking dialog and returns structured intent.

- [ ] `agent/prompts.py` — system prompt with business hours, JSON output format, few-shot examples
- [ ] `agent/schemas.py` — Pydantic `AgentResponse` model
- [ ] `agent/conversation.py` — `process_turn(chat_id, user_text)` → `AgentResponse`
- [ ] Wire `ConversationManager` into `/webhook` in `app.py`
- [ ] Test with simulated messages (no Telegram needed yet)

### Phase 4 — Google Calendar Integration (Day 3)

**Goal:** Real availability checks and event creation.

- [ ] Set up Google Cloud project + service account
- [ ] Share business calendar with service account email
- [ ] `calendar_service/google_cal.py`
  - `check_availability(slot)` → freebusy API
  - `create_event(name, telegram_user, slot)` → returns event ID
- [ ] Add 5-minute SQLite cache for availability to reduce API calls

### Phase 5 — Integration + Polish (Day 3–4)

**Goal:** Fully working end-to-end booking flow.

- [ ] Full flow test: name → datetime → confirm → booking in SQLite + Google Calendar
- [ ] Handle edge cases: unrecognized dates, already-booked slots, user cancels
- [ ] Telegram webhook signature validation (prevent spoofed requests)
- [ ] Graceful fallback message if Gemini or Calendar API fails

### Phase 6 — Deploy (Day 4–5)

**Goal:** Bot running 24/7 on a free server.

- [ ] Deploy to Render free tier (or Railway)
- [ ] Set environment variables in dashboard
- [ ] Register Telegram webhook to production URL
- [ ] Smoke test end-to-end from real Telegram on Airtel phone

---

## Key Dependencies

| Package | Why |
|---|---|
| `flask` | Telegram webhooks are simple HTTP POSTs |
| `google-generativeai` | Gemini Flash SDK — free tier, no credit card |
| `python-telegram-bot` | Telegram Bot API wrapper (or use raw `requests`) |
| `google-api-python-client` | Google Calendar REST client |
| `google-auth` | Service account authentication |
| `pydantic` | Validate Gemini's structured JSON output |
| `python-dotenv` | Load `.env` file |
| `gunicorn` | Production WSGI server |

---

## Environment Variables

```bash
# Telegram
TELEGRAM_BOT_TOKEN=xxxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Google Gemini (free at aistudio.google.com — no credit card)
GEMINI_API_KEY=AIzaxxxxxxxx

# Google Calendar
GOOGLE_SERVICE_ACCOUNT_FILE=credentials/service_account.json
GOOGLE_CALENDAR_ID=your-calendar@group.calendar.google.com

# App
BUSINESS_NAME="Your Business Name"
BUSINESS_HOURS="Monday-Friday, 9am-5pm"
APPOINTMENT_DURATION_MINUTES=60
```

---

## Verification Checklist

- [ ] Message bot "hi" → bot replies with greeting
- [ ] Full booking flow via Telegram: name → datetime → confirm → booking in SQLite
- [ ] Google Calendar event created on confirmation
- [ ] Message bot from Airtel phone → works end-to-end
- [ ] Bot handles "that slot is taken" gracefully

---

## Decisions Made

| Decision | Why |
|---|---|
| Telegram instead of phone | Completely free, no credit card, works on Airtel phone via app |
| `gemini-1.5-flash` | Free tier (no credit card), fast (~500ms), generous daily limits |
| SQLite for MVP | Zero-ops, fast reads, easy to migrate to Postgres later |
| Service account for Google | No OAuth consent screen complexity for server-side MVP |
| Session stored in SQLite by `chat_id` | Telegram provides stable `chat_id` per user; same pattern as `CallSid` |
| Flask webhooks over polling | Webhooks are more reliable and work the same way as the future Twilio upgrade |
