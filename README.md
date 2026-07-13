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
| AI / LLM | Google Gemini Flash 1.5 | Free tier |
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
    └── .gitkeep                  # Put Google service account JSON here
```

---

## Setup

### 1. Create Telegram Bot

1. Open Telegram, message [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts
3. Copy the bot token

### 2. Get Gemini API Key

1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Sign in with Google (free, no credit card)
3. Click **Get API Key** → Create API key
4. Copy the key

### 3. Set Up Google Calendar

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project → Enable **Google Calendar API**
3. Create a **Service Account** → Download JSON key
4. Place JSON file at `credentials/service_account.json`
5. Share your Google Calendar with the service account email (give it edit access)
6. Copy your calendar ID (Settings → Integrate calendar)

### 4. Install & Run

```bash
# Clone the repo
git clone https://github.com/aniketshaw29/appointment-booking-agent.git
cd appointment-booking-agent

# Install dependencies
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
| [FUTURE_PHONE.md](FUTURE_PHONE.md) | Migration guide to phone calling with Twilio |

---

## Environment Variables

See [.env.example](.env.example) for the full list. Required:

```
TELEGRAM_BOT_TOKEN     — from @BotFather
GEMINI_API_KEY         — from aistudio.google.com
GOOGLE_CALENDAR_ID     — your calendar ID
GOOGLE_SERVICE_ACCOUNT_FILE — path to service account JSON
```
