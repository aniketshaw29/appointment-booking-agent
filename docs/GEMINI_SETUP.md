# Gemini API Setup

This guide gets you a free Google Gemini API key — no credit card required.

---

## Step 1 — Go to Google AI Studio

1. Open [aistudio.google.com](https://aistudio.google.com)
2. Sign in with your Google account (the same one as your project: **Aniket Appointment booking app**)

---

## Step 2 — Create an API Key

1. Click **Get API Key** in the top left
2. Click **Create API key**
3. Select your existing project: **Aniket Appointment booking app**
4. Click **Create API key in existing project**
5. Copy the key — it starts with `AIza...`

---

## Step 3 — Add to .env

```bash
GEMINI_API_KEY=AIzaxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Free Tier Limits

| Model | Requests/min | Requests/day |
|---|---|---|
| Gemini 2.0 Flash | 15 | 200 |

> If you hit the daily limit, create a new API key in AI Studio or wait until midnight Pacific time for it to reset.

---

## Verify It's Working

```bash
python - << 'EOF'
import os
os.environ["GEMINI_API_KEY"] = "your-key-here"

import google.generativeai as genai
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")
resp = model.generate_content("Say hello in one word")
print(f"✅ Gemini response: {resp.text.strip()}")
EOF
```

If you see `✅ Gemini response: Hello` (or similar), the key works.
