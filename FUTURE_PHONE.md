# Future Upgrade — Phone Calling Agent

This doc tracks what needs to change when you're ready to upgrade from the Telegram bot to a real phone calling agent.

## What Changes

| Component | Telegram (current) | Phone (future) |
|---|---|---|
| Channel | Telegram Bot API | Twilio |
| User input | Text messages | Voice → Twilio STT |
| Bot output | Telegram messages | TwiML `<Say>` |
| Session key | `chat_id` | `CallSid` |
| Webhook trigger | `POST /webhook` (Telegram update) | `POST /incoming` + `POST /gather` |
| Cost | Free | ~$0.40/call + $1.15/month number |

## What Stays the Same

- `agent/conversation.py` — ConversationManager is unchanged
- `agent/prompts.py` — same system prompt works for both
- `agent/schemas.py` — same Pydantic models
- `calendar_service/` — Google Calendar + SQLite untouched
- `config.py` — just add Twilio vars

## Migration Steps (when ready)

1. **Sign up for Twilio** (needs credit card, ~$1.15/month for Indian number)
2. **Add `telephony/twiml_builder.py`** — `say_and_gather(text)` and `say_and_hangup(text)` helpers
3. **Add routes to `app.py`**:
   - `POST /incoming` — answers the call, plays greeting
   - `POST /gather` — receives `SpeechResult`, calls `ConversationManager`, returns TwiML
4. **Add Twilio request validation** — verify webhook POST is from Twilio (prevent spoofing)
5. **Update session key** — swap `chat_id` for `CallSid` in `db.py`
6. **Add env vars**: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`
7. **Keep Gemini** — same LLM, no change needed

## New Dependencies for Phone

```
twilio          # TwiML generation + webhook signature validation
```

## New Environment Variables for Phone

```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxx
TWILIO_PHONE_NUMBER=+91xxxxxxxxxx
```

## Twilio India Pricing Reference

| Item | Cost |
|---|---|
| Indian phone number | $1.15 / month |
| Inbound call (mobile) | $0.0496 / min |
| Speech recognition per turn | $0.02 / turn |
| Per booking call (~5 min, 7 turns) | ~$0.39 |

At 20 test calls/month → ~$12–15/month total.
