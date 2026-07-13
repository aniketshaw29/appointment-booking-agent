# Appointment Booking Agent

An AI-powered appointment booking bot built with Telegram, Google Gemini Flash, and Google Calendar. Users chat with the bot naturally to book appointments — the AI handles the conversation, checks calendar availability, and confirms the booking.

**Telegram:** [@aniketshaw_appointment_bot](https://t.me/aniketshaw_appointment_bot)

> **Future upgrade:** Swap the Telegram layer for Twilio to turn this into a real phone calling agent. See [FUTURE_PHONE.md](FUTURE_PHONE.md).

---

## What It Does

1. User messages the Telegram bot
2. Bot collects their name and preferred appointment time
3. Checks Google Calendar for availability
4. Confirms the booking (or offers an alternative slot)
5. Saves to SQLite + creates a Google Calendar event

## Stack

| Component | Tech | Cost |
|---|---|---|
| Messaging | Telegram Bot API | Free |
| AI / LLM | Google Gemini 2.0 Flash | Free tier |
| Calendar | Google Calendar API | Free |
| Database | SQLite | Free |
| Backend | Python + Flask | Free |
| Hosting (dev) | ngrok | Free |
| Hosting (prod) | Render free tier | Free |

**Total cost: $0. No credit card required anywhere.**

---

## Project Structure

```
appointment-booking-agent/
├── app.py                        # Flask entry point, Telegram webhook handler
├── config.py                     # Env var loading
├── requirements.txt
├── .env.example                  # Copy to .env and fill in your keys
│
├── agent/
│   ├── conversation.py           # ConversationManager — calls Gemini
│   ├── prompts.py                # System prompt
│   └── schemas.py                # Pydantic models for structured output
│
├── calendar_service/
│   ├── google_cal.py             # Google Calendar API wrapper
│   └── db.py                    # SQLite sessions + bookings
│
├── telephony/
│   └── telegram_sender.py       # Telegram sendMessage helper
│
└── credentials/
    └── .gitkeep                  # Put Google service account JSON here (gitignored)
```

---

## Setup

### 1. Create Telegram Bot

See [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md) for the full step-by-step guide.

Quick summary:
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` → follow prompts → copy the token

### 2. Get Gemini API Key

See [GEMINI_SETUP.md](GEMINI_SETUP.md) for the full step-by-step guide.

Quick summary:
1. Go to [aistudio.google.com](https://aistudio.google.com) — free, no credit card
2. Click **Get API Key** → create key in your project → copy it

### 3. Set Up Google Calendar

See [GOOGLE_CALENDAR_SETUP.md](GOOGLE_CALENDAR_SETUP.md) for the full step-by-step guide.

Quick summary:
1. Enable Google Calendar API in Cloud Console
2. Create a Service Account → download JSON key → place at `credentials/service_account.json`
3. Share your calendar with `aniket-appointment-bot@aniket-appointment-booking-app.iam.gserviceaccount.com`

### 4. Install & Run

```bash
# Clone the repo
git clone https://github.com/aniketshaw29/appointment-booking-agent.git
cd appointment-booking-agent

# Install dependencies (use Python 3.12)
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your keys

# Run locally
python app.py

# In another terminal, expose via ngrok
ngrok http 5000

# Register webhook with Telegram
curl "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=https://<ngrok-url>/webhook"
```

---

## Documentation

| File | Contents |
|---|---|
| [PLAN.md](PLAN.md) | Phased build plan with checklist |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System diagram and request lifecycle |
| [CONVERSATION_FLOW.md](CONVERSATION_FLOW.md) | Dialog state machine and sample conversation |
| [COST.md](COST.md) | Cost analysis and free tier breakdown |
| [RUNNING_THE_BOT.md](RUNNING_THE_BOT.md) | How to run locally with ngrok or deploy to Render |
| [DEPLOY.md](DEPLOY.md) | Full Render deployment guide |
| [CLIENT_BOOKING_GUIDE.md](CLIENT_BOOKING_GUIDE.md) | How clients can start a booking via Telegram |
| [FUTURE_PHONE.md](FUTURE_PHONE.md) | Migration guide to phone calling with Twilio |
| [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md) | Get your Telegram bot token from @BotFather |
| [GEMINI_SETUP.md](GEMINI_SETUP.md) | Get your free Gemini API key |
| [GOOGLE_CALENDAR_SETUP.md](GOOGLE_CALENDAR_SETUP.md) | Set up Google Calendar service account |

---

## Environment Variables

See [.env.example](.env.example) for the full list. Required:

```
TELEGRAM_BOT_TOKEN          — from @BotFather  → TELEGRAM_SETUP.md
GEMINI_API_KEY              — from aistudio.google.com  → GEMINI_SETUP.md
GOOGLE_CALENDAR_ID          — your calendar ID  → GOOGLE_CALENDAR_SETUP.md
GOOGLE_SERVICE_ACCOUNT_FILE — path to service account JSON  → GOOGLE_CALENDAR_SETUP.md
```
