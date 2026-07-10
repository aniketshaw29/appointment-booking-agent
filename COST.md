# Cost Analysis — Appointment Booking Agent

## Your Context
- Location: India
- Number: Airtel postpaid (mobile)
- Purpose: Learning + experimental project

---

## Current Stack — 100% Free

| Component | Service | Cost |
|---|---|---|
| Messaging | Telegram Bot API | Free |
| LLM | Google Gemini Flash free tier | Free |
| Calendar | Google Calendar API | Free |
| Database | SQLite | Free |
| Dev hosting | ngrok free tier | Free |
| Prod hosting | Render free tier | Free |

**Total: $0. No credit card required anywhere.**

Get your Gemini key at [aistudio.google.com](https://aistudio.google.com) — sign in with Google, no payment needed.

---

## Future Stack — Phone Calling (when ready)

### Twilio (India pricing)

| Item | Cost |
|---|---|
| Indian phone number (monthly) | $1.15 / month |
| Inbound call — mobile caller | $0.0496 / min |
| Inbound call — landline caller | $0.0699 / min |
| Speech recognition (per turn) | $0.02 / turn |

**Per booking call estimate (5 min, 7 dialog turns):**
- Call minutes: 5 × $0.0496 = **$0.25**
- STT turns: 7 × $0.02 = **$0.14**
- Total per call: **~$0.39**

### Monthly Cost at Different Volumes

| Test calls / month | Twilio number | Call + STT | Gemini | **Total** |
|---|---|---|---|---|
| 10 calls | $1.15 | $3.90 | ~$0 | **~$5** |
| 50 calls | $1.15 | $19.50 | ~$0 | **~$21** |
| 100 calls | $1.15 | $39.00 | ~$0 | **~$41** |

See [FUTURE_PHONE.md](FUTURE_PHONE.md) for the migration guide.
