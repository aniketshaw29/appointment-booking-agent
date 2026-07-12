# Cost Analysis — Appointment Booking Calling Agent

## Your Context
- Location: India
- Number: Airtel postpaid (mobile)
- Purpose: Learning + experimental project

---

## Paid Stack — What Things Actually Cost

### Twilio (India pricing)

| Item | Cost |
|---|---|
| Indian phone number (monthly) | $1.15 / month |
| Inbound call — mobile caller | $0.0496 / min |
| Inbound call — landline caller | $0.0699 / min |
| Speech recognition (per `<Gather>` turn) | $0.02 / turn |

**Per booking call estimate (5 min, 7 dialog turns):**
- Call minutes: 5 × $0.0496 = **$0.25**
- STT turns: 7 × $0.02 = **$0.14**
- Total per call: **~$0.39**

### Claude Haiku 4.5 (Anthropic)

| Item | Cost |
|---|---|
| Input tokens | $1.00 / 1M tokens |
| Output tokens | $5.00 / 1M tokens |

**Per booking call estimate (7 turns, ~500 input + 100 output tokens each):**
- Input: 3,500 tokens × ($1 / 1M) = **$0.0035**
- Output: 700 tokens × ($5 / 1M) = **$0.0035**
- Total per call: **~$0.007** — essentially free

### Google Calendar API
**Free.** 1,000,000 requests/day on personal Google accounts. No charge.

### SQLite
**Free.** Zero-ops, no server, no cost.

---

## Monthly Cost at Different Volumes

| Test calls / month | Twilio number | Call + STT | Claude | **Total** |
|---|---|---|---|---|
| 10 calls | $1.15 | $3.90 | $0.07 | **~$5** |
| 50 calls | $1.15 | $19.50 | $0.35 | **~$21** |
| 100 calls | $1.15 | $39.00 | $0.70 | **~$41** |

For a learning project, **10–20 test calls/month** → **under $10/month total.**

---

## Free Alternatives for Every Component

### 1. LLM — Replace Claude

| Option | Free tier | Speed | Notes |
|---|---|---|---|
| **Groq** (Llama 3.1 70B) | Yes — generous | Very fast (~200ms) | Best free option for voice latency |
| **Google Gemini Flash** | Yes — free tier | Fast | Good, easy to set up |
| **Ollama (local)** | Completely free | Depends on hardware | Runs on your Mac; no API cost ever |
| **Mistral API** | Trial credits | Fast | Llama-based, good quality |

**Best free pick for this project:** Groq (free tier, fastest response, Python SDK similar to OpenAI's)

**Why not keep Claude free?** Anthropic has no free tier — you pay per token. But costs are tiny (~$0.007/call with Haiku 4.5). For a learning project, Groq or local Ollama makes sense to start.

---

### 2. Voice/Telephony — Replace Twilio (Paid)

Twilio doesn't have a permanent free tier, but:

| Option | What you get free | Good enough for... |
|---|---|---|
| **Twilio Trial** | $15.50 credit (~40 test calls) | Getting started, first few weeks of testing |
| **Plivo Trial** | $0.05 credit (very small) | Not useful |
| **Signalwire** | Trial credits | Similar to Twilio, slightly cheaper |
| **Vapi.ai** | Free tier — 10 min/month | Not enough for real testing |

**Honest assessment:** Truly free inbound phone calling to an Indian number is very hard. Twilio's $15.50 trial is your best "free" option — it buys ~40 test calls with full functionality.

**India-specific trick:** You can get a **US Twilio trial number for free** and call it using a VoIP app (Google Voice, etc.) from your laptop for testing — no Airtel charges. When you're ready to test from a real phone, spend $1.15/month on an Indian number.

---

### 3. Speech-to-Text (STT) — Free Options

Twilio's `<Gather input="speech">` includes basic STT built-in (the $0.02/turn above). But you can replace it:

| Option | Cost | Quality | How |
|---|---|---|---|
| **Twilio built-in** | $0.02/turn | Good for phone calls | Default — no change needed |
| **Deepgram** | $200 free credit | Excellent | Replace Twilio STT via `<Start><Stream>` |
| **AssemblyAI** | Free tier (100 min/month) | Good | More complex to wire up |
| **OpenAI Whisper (local)** | Free | Excellent | Run locally via `openai-whisper` pip package |

For the MVP, **just use Twilio's built-in STT** — it's already wired into `<Gather>` at $0.02/turn, and the simplest path. Come back to this if quality is bad.

---

### 4. Calendar — Already Free

Google Calendar API is free. No action needed.

---

## Recommended Free Setup for Learning

```
Messaging     → Telegram Bot API (completely free, no credit card)
LLM           → Google Gemini Flash free tier (no credit card, get key at aistudio.google.com)
Calendar      → Google Calendar API (free)
Database      → SQLite (free)
Hosting       → ngrok (free tier) for local dev; Render free tier for production
```

**Total cost: $0, no credit card required anywhere**

---

## Code Changes for Free Stack

### Swap Claude → Groq

```python
# requirements.txt: add groq
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

response = client.chat.completions.create(
    model="llama-3.1-70b-versatile",  # fast, free
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        *conversation_history,
        {"role": "user", "content": user_text},
    ],
    response_format={"type": "json_object"},
    max_tokens=512,
)
result = json.loads(response.choices[0].message.content)
```

The Groq SDK is nearly identical to OpenAI's. Response format and latency work well for phone conversations.

### Keep Twilio (trial covers dev phase)

No code change needed — just use trial account. The webhook code is identical whether on trial or paid.

---

## Summary Table

| Component | Free option | Monthly cost (paid) |
|---|---|---|
| LLM | Groq free tier | ~$0.35 (100 calls w/ Haiku) |
| Phone number | Twilio trial ($15.50) | $1.15 |
| Inbound calls | — | ~$0.25–0.40 / call |
| STT | Built into Twilio | Included above |
| TTS | Built into Twilio | Included above |
| Calendar API | Free always | $0 |
| Database (SQLite) | Free always | $0 |
| Dev hosting (ngrok) | Free tier | $0 |

**For a learning project doing 20 test calls/month:**
- Free stack (Groq + Twilio trial): **$0** for weeks
- When trial runs out: **~$12–15/month** all-in
