# Architecture

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        TELEGRAM USER                             │
│  Sends message → Telegram servers → POST to /webhook             │
│  ← Bot reply via Telegram sendMessage API                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │  HTTP POST
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FLASK APP (app.py)                           │
│                                                                   │
│   GET  /          → Landing page (auto-redirect to Telegram)    │
│   GET  /admin     → Model switcher dashboard (password-protected)│
│   POST /webhook   → Telegram message handler                    │
│   GET  /health    → Status check (includes active model)        │
│                                                                   │
│   /webhook flow:                                                  │
│   ├── validate Telegram secret                                   │
│   ├── load session (SQLite by chat_id)                           │
│   ├── agent/llm.process_turn(chat_id, text, model_id)           │
│   ├── if check_availability → Google Calendar freebusy          │
│   ├── if book → SQLite + Google Calendar create event           │
│   └── send reply via Telegram API                               │
└───────┬──────────────────┬──────────────────────────────────────┘
        │                  │
        ▼                  ▼
┌──────────────────┐  ┌──────────────────────────────────────────┐
│   LLM ROUTER     │  │           CALENDAR LAYER                 │
│   agent/llm.py   │  │                                           │
│                  │  │  ┌────────────────┐  ┌────────────────┐  │
│  Active model    │  │  │ Google Calendar│  │  SQLite DB     │  │
│  (runtime toggle)│  │  │ - freebusy API │  │  - sessions    │  │
│                  │  │  │ - create event │  │  - bookings    │  │
│  ┌─────────────┐ │  │  └────────────────┘  └────────────────┘  │
│  │Gemini 2.5   │ │  └──────────────────────────────────────────┘
│  │Gemini 2.0   │ │
│  │GPT-4o-mini  │ │
│  │GPT-4o       │ │
│  └─────────────┘ │
└──────────────────┘
        ▲
        │ admin toggles via /admin
        │
┌──────────────────┐
│  ADMIN PANEL     │
│  /admin          │
│  Password-gated  │
│  Runtime switch  │
│  No restart needed│
└──────────────────┘
```

## Request Lifecycle (single user message)

1. User sends message on Telegram → Telegram POSTs update to `/webhook`
2. Flask validates Telegram webhook secret (403 if invalid)
3. Session loaded from SQLite by `chat_id`
4. `agent/llm.process_turn(chat_id, text, active_model)` called
5. LLM router picks Gemini or OpenAI based on active model
6. LLM returns JSON: `{reply_text, action, extracted_name, extracted_age, extracted_location, extracted_nature, extracted_purpose, proposed_slot}`
7. If `action == "check_availability"`: validates slot isn't in past, queries Google Calendar freebusy
8. If `action == "book"`: creates Google Calendar event, writes booking to SQLite
9. Flask calls Telegram `sendMessage` with the reply
10. Session state saved back to SQLite

## LLM Routing

All AI calls go through `agent/llm.py` — a unified router that picks the right provider:

| Model ID | Provider | Free? |
|---|---|---|
| `gemini-2.5-flash` | Google Generative AI | ✅ Free tier |
| `gemini-2.0-flash` | Google Generative AI | ✅ Free tier |
| `gpt-4o-mini` | OpenAI | ❌ Paid |
| `gpt-4o` | OpenAI | ❌ Paid |

The active model is set via `ACTIVE_MODEL` env var on startup and can be changed at runtime via the admin panel (`/admin`) without a restart.

## Admin Panel

Password-protected dashboard at `/admin`:
- Shows currently active model and OpenAI key status
- Click any model card to switch — takes effect on the next message
- GPT models are greyed out (locked) until `OPENAI_API_KEY` is set
- `ACTIVE_MODEL` env var = persistent default; admin panel = runtime override (resets on restart)

## Response Time Budget

| Component | Target |
|---|---|
| Flask routing + validation | < 20ms |
| SQLite read | < 10ms |
| Gemini 2.5 Flash | 400–900ms |
| GPT-4o-mini | 500–1200ms |
| Google Calendar API (when needed) | 200–500ms |
| SQLite write | < 10ms |
| Telegram sendMessage | < 200ms |
| **Total per turn** | **< 1.5–2 seconds** |

## Error Handling

All errors are typed and map to user-friendly Telegram messages:

| Exception | User sees |
|---|---|
| `GeminiQuotaError` | "Getting a lot of requests, try in a few minutes" |
| `GeminiError` | "Having trouble thinking, send /start and retry" |
| `CalendarAuthError` | "Configuration issue — contact the business directly" |
| `CalendarError` | "Couldn't reach the calendar, try in a moment" |
| `BookingConflictError` (past slot) | "That date has already passed, pick a future date" |

## Security

- **Env vars** for all secrets — never hardcoded
- **Service account JSON** gitignored — stored in `credentials/` only
- **Telegram webhook secret** — validates POST is from Telegram
- **Admin panel** — password-gated via Flask session (HMAC compare)
- **Idempotency** on booking insert — UNIQUE constraint prevents duplicates
