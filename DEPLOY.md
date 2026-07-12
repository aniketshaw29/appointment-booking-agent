# Deploy to Render (Free Tier)

Render's free tier keeps the bot running 24/7 at no cost. No credit card required.

---

## Step 1 — Sign Up for Render

1. Go to [render.com](https://render.com)
2. Sign up with your GitHub account (`aniketshaw29`)
3. Authorize Render to access your repositories

---

## Step 2 — Create a Web Service

1. Dashboard → **New** → **Web Service**
2. Connect repository: `aniketshaw29/appointment-booking-agent`
3. Settings:
   - **Name:** `appointment-booking-agent`
   - **Runtime:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** Free

---

## Step 3 — Add Environment Variables

In the Render dashboard → **Environment** tab, add each of these:

| Key | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Your bot token from @BotFather |
| `GEMINI_API_KEY` | Your key from aistudio.google.com |
| `GOOGLE_CALENDAR_ID` | Your calendar ID |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | `credentials/service_account.json` |
| `BUSINESS_NAME` | Your business name |
| `BUSINESS_HOURS` | e.g. `Monday-Friday, 9am-5pm` |
| `APPOINTMENT_DURATION_MINUTES` | `60` |
| `TELEGRAM_WEBHOOK_SECRET` | Any random string (e.g. `mysecret123`) |

---

## Step 4 — Upload Google Service Account JSON

The service account JSON can't go in the repo (it's gitignored). Add it as a **Secret File** on Render:

1. Render dashboard → your service → **Environment** → **Secret Files**
2. **Filename:** `credentials/service_account.json`
3. **Contents:** paste the full JSON from your downloaded service account file
4. Save

---

## Step 5 — Deploy

1. Click **Deploy** — Render builds and starts the service
2. Copy your service URL: `https://appointment-booking-agent.onrender.com`

---

## Step 6 — Register Telegram Webhook

```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=https://appointment-booking-agent.onrender.com/webhook&secret_token=<YOUR_WEBHOOK_SECRET>"
```

Replace `<YOUR_TOKEN>` and `<YOUR_WEBHOOK_SECRET>` with your values.

Verify it worked:
```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo"
```

---

## Step 7 — Test

Message your bot on Telegram from your Airtel phone. Full booking flow should work end-to-end.

---

## Notes

- **Free tier sleeps after 15 min of inactivity** — the first message after a sleep takes ~30 seconds to respond. This is fine for testing. Upgrade to a paid plan ($7/month) for always-on production.
- **SQLite resets on each deploy** — bookings stored in SQLite are lost when Render redeploys. For production, switch to Render's managed Postgres (free tier available).
