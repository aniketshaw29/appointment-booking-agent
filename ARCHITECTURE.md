# Architecture

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        TELEGRAM USER                             │
│  Sends message → Telegram servers → POST to webhook              │
│  ← Bot reply via Telegram Bot API sendMessage                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │  HTTP POST (Telegram webhook)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FLASK APP (app.py)                           │
│                                                                   │
│   POST /webhook ──── parse Telegram update                      │
│                 │                                                 │
│                 ├── load session (SQLite by chat_id)             │
│                 ├── ConversationManager.process_turn()           │
│                 ├── if check_availability: → Google Cal          │
│                 ├── if book: → SQLite + Google Cal               │
│                 └── send reply via Telegram API                  │
└───────┬──────────────────┬──────────────────────────────────────┘
        │                  │
        ▼                  ▼
┌──────────────┐   ┌──────────────────────────────────────────────┐
│  GEMINI API  │   │           CALENDAR LAYER                     │
│              │   │                                               │
│  Model:      │   │  ┌──────────────────┐  ┌──────────────────┐ │
│  Flash 1.5   │   │  │  Google Calendar │  │  SQLite DB        │ │
│              │   │  │  - freebusy API  │  │  - sessions       │ │
│  - Extract   │   │  │  - create event  │  │  - bookings       │ │
│    intent    │   │  └──────────────────┘  └──────────────────┘ │
│  - Manage    │   │       (5-min cache in SQLite)                │
│    dialog    │   └──────────────────────────────────────────────┘
│  - JSON out  │
└──────────────┘
```

## Request Lifecycle (single user message)

1. User sends message on Telegram → Telegram POSTs update to `/webhook`
2. Flask parses `update.message.text` and `update.message.chat.id`
3. Session loaded from SQLite by `chat_id`
4. `ConversationManager.process_turn(chat_id, message_text)` called
5. Gemini returns JSON: `{reply_text, action, extracted_name, proposed_slot}`
6. If `action == "check_availability"`: query Google Calendar (or SQLite cache)
7. If `action == "book"`: write booking to SQLite, create Google Calendar event
8. Flask calls Telegram `sendMessage` API with the reply text
9. Session state saved back to SQLite

## Response Time Budget

| Component | Target |
|---|---|
| Flask routing | < 20ms |
| SQLite read | < 10ms |
| Gemini Flash 1.5 | 300–800ms |
| Google Calendar API (when needed) | 200–500ms |
| SQLite write | < 10ms |
| Telegram sendMessage | < 200ms |
| **Total per turn** | **< 1.5 seconds** |

## Why These Choices

| Choice | Rationale |
|---|---|
| Telegram Bot API | Completely free, no credit card, works on any phone |
| Gemini Flash 1.5 | Free tier at aistudio.google.com; fast enough for chat |
| Flask (not FastAPI) | Telegram webhooks are synchronous; async gives no benefit |
| SQLite | Zero-ops for MVP; trivial migration path to Postgres |
| Service account (not OAuth) | Server-side app; no user consent flow needed |
| Webhooks over polling | More reliable; same pattern as future Twilio upgrade |

## Security Considerations

- **Env vars** for all secrets — never hardcoded
- **Service account JSON** gitignored — stored in `credentials/` only
- **Telegram webhook secret token** — validates POST is from Telegram, not spoofed
- **Idempotency** on booking insert — prevents duplicate records on retries
