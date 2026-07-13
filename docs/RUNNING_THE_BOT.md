# How to Run the Bot

The bot needs a **public HTTPS URL** so Telegram can send messages to it. Two options:

---

## Option A — Local Dev with ngrok (Test Right Now, Free)

Run the bot on your laptop and expose it via ngrok. Good for testing — not permanent.

### Step 1 — Install ngrok

```bash
brew install ngrok
```

Or download from [ngrok.com/download](https://ngrok.com/download).

### Step 2 — Start the bot

```bash
cd /Users/I528803/Documents/2-personal/coding-stuff/appointment-booking-agent
source .venv/bin/activate
python app.py
```

You should see:
```
* Running on http://127.0.0.1:5000
```

### Step 3 — Expose it publicly

In a **second terminal**:

```bash
ngrok http 5000
```

ngrok gives you a URL like:
```
https://abc123.ngrok-free.app
```

### Step 4 — Register the webhook with Telegram

```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=https://abc123.ngrok-free.app/webhook"
```

You should see:
```json
{"ok":true,"result":true,"description":"Webhook was set"}
```

### Step 5 — Test it

Open Telegram → search `@aniketshaw_appointment_bot` → send `/start`.

### Limitations of ngrok free tier

- URL changes every time you restart ngrok → you must re-register the webhook each time
- Bot stops working when your laptop sleeps or closes
- Only use this for local testing

---

## Option B — Deploy to Render (Permanent, Free, No Credit Card)

Render hosts the bot 24/7 so it works even when your laptop is off. Full steps in [DEPLOY.md](DEPLOY.md).

### Quick Steps

1. Go to [render.com](https://render.com) → **Sign up with GitHub**
2. New → **Web Service** → connect repo `aniketshaw29/appointment-booking-agent`
3. Settings:
   - **Runtime:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** Free
4. Add all env vars (copy from your `.env` file)
5. Add `credentials/service_account.json` as a **Secret File** (see [DEPLOY.md](DEPLOY.md))
6. Click **Deploy** → wait ~2 minutes
7. Copy your URL: `https://appointment-booking-agent.onrender.com`
8. Register webhook **once**:

```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=https://appointment-booking-agent.onrender.com/webhook"
```

Done — bot runs permanently.

### Render Free Tier Notes

| Thing | Detail |
|---|---|
| Cost | Free (no credit card) |
| Always on? | Sleeps after 15 min of no traffic — first message takes ~30s to wake up |
| SQLite persistence | Resets on each deploy (use Postgres for production) |
| Upgrade cost | $7/month for always-on |

---

## Which Should I Use?

| Situation | Use |
|---|---|
| Testing locally, building features | ngrok (Option A) |
| Sharing with real clients | Render (Option B) |
| Production / always-on | Render paid tier ($7/month) |

---

## Verify Your Webhook is Registered

```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo"
```

Should show your URL and `"pending_update_count": 0`.

## Remove the Webhook (if needed)

```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/deleteWebhook"
```
