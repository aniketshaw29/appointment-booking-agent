# Verify skill — appointment-booking-agent

## Environment

Python 3.14 is the default but pydantic-core has no wheel for it.
Use Python 3.12 (Homebrew):

```bash
rm -rf .venv
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt -q
```

## Run tests

The app needs real env vars but no live credentials for unit/integration tests.
Patch Gemini + Telegram, use a temp SQLite DB:

```bash
.venv/bin/python - << 'EOF'
import os, sys
sys.path.insert(0, ".")
os.environ.update({
    "TELEGRAM_BOT_TOKEN": "123456:TEST",
    "GEMINI_API_KEY": "TEST",
    "GOOGLE_SERVICE_ACCOUNT_FILE": "credentials/service_account.json",
    "GOOGLE_CALENDAR_ID": "test@calendar.google.com",
    "BUSINESS_NAME": "Test Clinic",
    "BUSINESS_HOURS": "Monday-Friday, 9am-5pm",
    "APPOINTMENT_DURATION_MINUTES": "60",
    "TELEGRAM_WEBHOOK_SECRET": "",
})
# ... test body using unittest.mock to patch google.generativeai and app.send_message
EOF
```

## Key surfaces to test

1. `GET /health` → 200 + business name
2. `POST /webhook` bad body → graceful 200
3. `POST /webhook` `/start` → greeting sent via `app.send_message`
4. `POST /webhook` `/cancel` → cancellation reply
5. Webhook secret: no header → 403; wrong → 403; correct → 200
6. DB: sessions CRUD, bookings UNIQUE constraint, range query
7. `AgentResponse` Pydantic model: valid actions pass, invalid raises ValidationError

## Gotchas

- Always mock `app.send_message` (not `telephony.telegram_sender.send_message`) after `app` is imported — otherwise the real requests.post fires against `123456:TEST` and fails
- `create_booking` returns `0` (not `None`) on duplicate due to `INSERT OR IGNORE`
- Webhook secret validation reads from `config.TELEGRAM_WEBHOOK_SECRET` at request time — safe to mutate between tests
