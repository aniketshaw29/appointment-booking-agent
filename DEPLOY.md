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
| `GOOGLE_CALENDAR_ID` | `aniketshawoffice@gmail.com` |
| `BUSINESS_NAME` | `Aniket Shaw` |
| `BUSINESS_HOURS` | `Monday-Friday, 5pm-9pm` |
| `APPOINTMENT_DURATION_MINUTES` | `30` |
| `TELEGRAM_WEBHOOK_SECRET` | Any random string — e.g. `apptbot2026` (save this, you need it in Step 6) |

> ⚠️ Do **not** add `GOOGLE_SERVICE_ACCOUNT_FILE` — it's handled automatically via the Secret File in Step 4.

---

## Step 4 — Upload Google Service Account JSON

The service account JSON can't go in the repo (it's gitignored). Add it as a **Secret File**:

1. Render dashboard → your service → **Environment** → **Secret Files**
2. **Filename:** `service_account.json`
   - Must be just the filename, no folder path (Render doesn't allow `/` in names)
   - Render places it at `/etc/secrets/service_account.json` automatically
3. **Contents:** paste the full JSON from your downloaded service account file
4. Click **Save**

`config.py` reads `/etc/secrets/service_account.json` by default on Render — no extra env var needed.

> ⚠️ Make sure you revoked the key that was accidentally shared and downloaded a fresh one before pasting here.

---

## Step 5 — Deploy

1. Click **Deploy** — Render builds and starts the service (~2 minutes)
2. Watch the build logs — you should see `Serving Flask app 'app'` at the end
3. Copy your service URL: `https://appointment-booking-agent.onrender.com`

If the build fails, check the logs for missing env vars.

---

## Step 6 — Register Telegram Webhook

Run this **once** (replace the placeholders):

```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=https://appointment-booking-agent.onrender.com/webhook&secret_token=<YOUR_WEBHOOK_SECRET>"
```

Expected response:
```json
{"ok":true,"result":true,"description":"Webhook was set"}
```

Verify:
```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo"
```

---

## Step 7 — Test

1. Open Telegram → search `@aniketshaw_appointment_bot`
2. Send `/start`
3. Complete the booking flow — confirm a Google Calendar event appears

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Build fails with `ModuleNotFoundError` | Check `requirements.txt` is committed and correct |
| Bot doesn't reply | Check webhook is registered: `getWebhookInfo` |
| `RuntimeError: Missing required environment variable` | Add the missing var in Render Environment tab |
| Calendar error | Check `service_account.json` was pasted correctly in Secret Files |
| Bot takes 30s to respond | Normal on free tier — it woke from sleep. Subsequent messages are instant |

---

## Notes

- **Free tier sleeps after 15 min of inactivity** — first message after sleep takes ~30 seconds. Fine for testing. Upgrade to $7/month for always-on.
- **SQLite resets on each deploy** — bookings are lost on redeploy. For production, switch to Render's managed Postgres (free tier available).
- **Python version** — if Render picks Python 3.14 and pydantic fails to install, add a `runtime.txt` file with `python-3.12.0`.
