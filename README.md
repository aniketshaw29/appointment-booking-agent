# Appointment Booking Agent

An AI-powered appointment booking bot built with Telegram, Google Gemini, and Google Calendar. Users chat with the bot naturally — the AI collects their details, checks calendar availability, and confirms the booking automatically.

**Live bot:** [@aniketshaw_appointment_bot](https://t.me/aniketshaw_appointment_bot)  
**Live site:** [appointment-booking-agent-p748.onrender.com](https://appointment-booking-agent-p748.onrender.com)

> **Future upgrade:** Swap Telegram for Twilio to turn this into a real phone calling agent. See [FUTURE_PHONE.md](FUTURE_PHONE.md).

---

## What It Does

1. User messages the Telegram bot
2. Bot collects name, age, location, nature of visit, and purpose
3. Asks for preferred appointment date and time
4. Checks Google Calendar availability in real time
5. Confirms booking (or offers the next free slot)
6. Saves to SQLite + creates a Google Calendar event

---

## Stack

| Component | Tech | Cost |
|---|---|---|
| Messaging | Telegram Bot API | Free |
| AI / LLM | Gemini 2.5 Flash (default) or GPT-4o / GPT-4o-mini | Free / Paid |
| Calendar | Google Calendar API | Free |
| Database | SQLite | Free |
| Backend | Python + Flask | Free |
| Hosting (dev) | ngrok | Free |
| Hosting (prod) | Render free tier | Free |

**Default stack cost: $0. No credit card required.**

---

## Admin Dashboard — Switch AI Models

The bot ships with a built-in admin panel at `/admin` to switch between AI models at runtime — no restart, no redeploy.

**Supported models:**

| Model | Provider | Cost | Notes |
|---|---|---|---|
| `gemini-2.5-flash` | Google | Free tier | Default — recommended |
| `gemini-2.0-flash` | Google | Free tier | Previous generation |
| `gpt-4o-mini` | OpenAI | Paid | Fast, cheap GPT |
| `gpt-4o` | OpenAI | Paid | Most capable GPT |

**How to access:**
1. Go to `https://<your-url>/admin`
2. Enter your `ADMIN_PASSWORD` (set via env var)
3. Pick a model → click **Apply Model**

GPT models show as locked until `OPENAI_API_KEY` is configured. The `ACTIVE_MODEL` env var sets the default on startup; the admin panel overrides it at runtime (resets on restart).

---

## Project Structure

```
appointment-booking-agent/
├── app.py                        # Flask entry point + admin routes
├── config.py                     # Env var loading
├── errors.py                     # Custom exceptions + user-facing messages
├── requirements.txt
├── .env.example
├── runtime.txt                   # Pins Python 3.12 for Render
├── Procfile                      # gunicorn start command
├── render.yaml                   # Render service config
│
├── agent/
│   ├── llm.py                    # Unified LLM router (Gemini + OpenAI)
│   ├── prompts.py                # System prompt
│   ├── schemas.py                # Pydantic AgentResponse model
│   └── conversation.py           # Legacy (kept for reference)
│
├── calendar_service/
│   ├── google_cal.py             # Google Calendar API wrapper
│   └── db.py                    # SQLite sessions + bookings
│
├── telephony/
│   └── telegram_sender.py       # Telegram sendMessage helper
│
├── templates/
│   ├── index.html                # Landing page (auto-redirects to bot)
│   ├── admin.html                # Admin dashboard
│   └── admin_login.html          # Admin login page
│
├── tests/
│   └── test_app.py              # 36 unit + integration tests
│
└── credentials/
    └── .gitkeep                  # Service account JSON goes here (gitignored)
```

---

## Setup

### 1. Create Telegram Bot

See [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md) — message [@BotFather](https://t.me/BotFather), send `/newbot`, copy the token.

### 2. Get Gemini API Key

See [GEMINI_SETUP.md](GEMINI_SETUP.md) — go to [aistudio.google.com](https://aistudio.google.com), free, no credit card.

### 3. Set Up Google Calendar

See [GOOGLE_CALENDAR_SETUP.md](GOOGLE_CALENDAR_SETUP.md) — enable API, create service account, share calendar.

### 4. Install & Run Locally

```bash
git clone https://github.com/aniketshaw29/appointment-booking-agent.git
cd appointment-booking-agent

# Python 3.12 required (3.14 breaks pydantic)
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Fill in your keys

python app.py
```

See [RUNNING_THE_BOT.md](RUNNING_THE_BOT.md) for ngrok setup and webhook registration.

### 5. Deploy to Render

See [DEPLOY.md](DEPLOY.md) for the full guide.

---

## Environment Variables

See [.env.example](.env.example) for the full list.

| Variable | Required | Description |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ✅ | From @BotFather |
| `GEMINI_API_KEY` | ✅ | From aistudio.google.com (free) |
| `GOOGLE_CALENDAR_ID` | ✅ | Your calendar ID |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | ✅ (local) | Path to service account JSON |
| `OPENAI_API_KEY` | ❌ | Only needed for GPT models |
| `ACTIVE_MODEL` | ❌ | Default model on startup (default: `gemini-2.5-flash`) |
| `ADMIN_PASSWORD` | ❌ | Password for `/admin` panel (default: `admin123`) |
| `TELEGRAM_WEBHOOK_SECRET` | ❌ | Validates webhook is from Telegram |
| `BUSINESS_NAME` | ❌ | Your business name |
| `BUSINESS_HOURS` | ❌ | e.g. `Monday-Friday, 5pm-9pm` |
| `APPOINTMENT_DURATION_MINUTES` | ❌ | Max 30 min (enforced) |

---

## Running Tests

```bash
.venv/bin/python -m pytest tests/ -v
```

36 tests covering DB, schemas, LLM routing, Flask routes, webhook handling, admin panel, and error messages. See [TESTING.md](TESTING.md).

---

## Documentation

| File | Contents |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System diagram, request lifecycle, LLM routing |
| [CONVERSATION_FLOW.md](CONVERSATION_FLOW.md) | Dialog state machine and sample conversation |
| [COST.md](COST.md) | Cost breakdown for current and future phone stack |
| [RUNNING_THE_BOT.md](RUNNING_THE_BOT.md) | Run locally with ngrok or deploy to Render |
| [DEPLOY.md](DEPLOY.md) | Full step-by-step Render deployment guide |
| [TESTING.md](TESTING.md) | How to run tests and what they cover |
| [CLIENT_BOOKING_GUIDE.md](CLIENT_BOOKING_GUIDE.md) | How clients start a booking via Telegram |
| [FUTURE_PHONE.md](FUTURE_PHONE.md) | Migration guide to Twilio phone calling |
| [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md) | Get Telegram bot token from @BotFather |
| [GEMINI_SETUP.md](GEMINI_SETUP.md) | Get free Gemini API key |
| [GOOGLE_CALENDAR_SETUP.md](GOOGLE_CALENDAR_SETUP.md) | Set up Google Calendar service account |
