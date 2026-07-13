# Cost Analysis

## Current Stack — Free by Default

| Component | Service | Cost |
|---|---|---|
| Messaging | Telegram Bot API | Free |
| AI / LLM | Google Gemini 2.5 Flash (free tier) | Free |
| Calendar | Google Calendar API | Free |
| Database | SQLite | Free |
| Dev hosting | ngrok free tier | Free |
| Prod hosting | Render free tier | Free |

**Default total: $0. No credit card required.**

Get your Gemini key at [aistudio.google.com](https://aistudio.google.com) — sign in with Google, no payment.

---

## AI Model Options and Cost

The bot supports multiple AI models, switchable from the admin panel at `/admin`:

| Model | Provider | Free? | Speed | Notes |
|---|---|---|---|---|
| `gemini-2.5-flash` | Google | ✅ Free | Fast | Default — recommended |
| `gemini-2.0-flash` | Google | ✅ Free | Fast | Previous generation |
| `gpt-4o-mini` | OpenAI | ❌ Paid | Fast | ~$0.002 per booking conversation |
| `gpt-4o` | OpenAI | ❌ Paid | Slower | ~$0.02 per booking conversation |

**Gemini free tier limits:** 15 requests/min, 200–1500 requests/day depending on model. More than enough for a personal/learning project.

**OpenAI cost estimate per booking (7 turns, ~500 tokens each):**
- GPT-4o-mini: ~$0.002 (essentially free at low volume)
- GPT-4o: ~$0.02 per conversation

---

## Future Stack — Phone Calling (Twilio)

When you upgrade to real phone calls (see [FUTURE_PHONE.md](FUTURE_PHONE.md)):

### Twilio India Pricing

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

### Monthly Cost at Different Volumes (Phone)

| Test calls / month | Twilio number | Call + STT | LLM | **Total** |
|---|---|---|---|---|
| 10 calls | $1.15 | $3.90 | ~$0 | **~$5** |
| 50 calls | $1.15 | $19.50 | ~$0 | **~$21** |
| 100 calls | $1.15 | $39.00 | ~$0 | **~$41** |

---

## Render Hosting Cost

| Plan | Cost | Notes |
|---|---|---|
| Free | $0 | Sleeps after 15 min inactivity; first message takes ~30s to wake |
| Starter | $7/month | Always-on, no sleep |

For a personal project: free tier is fine. For real clients: $7/month for always-on.
