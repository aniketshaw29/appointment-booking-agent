# How to Get Your Telegram Bot Token

A Telegram bot token looks like this: `7123456789:AAFabcDEFghiJKLmnoPQRstuVWXyz123456`

---

## Step-by-Step

### 1. Open Telegram and find BotFather

- Open the Telegram app on your phone or [web.telegram.org](https://web.telegram.org)
- In the search bar, type **@BotFather**
- Tap the official one (has a blue verified checkmark)

### 2. Start a chat

- Tap **Start** or send `/start`
- BotFather will show you a list of commands

### 3. Create a new bot

- Send: `/newbot`
- BotFather asks: **"What name would you like to give your bot?"**
  - This is the display name (e.g. `My Booking Bot`)
- BotFather asks: **"Now choose a username for your bot."**
  - Must end in `bot` (e.g. `mybooking_bot` or `MyBookingBot`)
  - Must be unique across all of Telegram

### 4. Copy your token

BotFather replies with something like:

```
Done! Congratulations on your new bot. You will find it at t.me/mybooking_bot.
You can now add a description, about section and profile picture for your bot...

Use this token to access the HTTP API:
7123456789:AAFabcDEFghiJKLmnoPQRstuVWXyz123456

Keep your token secure and store it safely...
```

**Copy the token** — it's the long string after `Use this token to access the HTTP API:`

### 5. Add it to your .env file

```bash
TELEGRAM_BOT_TOKEN=7123456789:AAFabcDEFghiJKLmnoPQRstuVWXyz123456
```

---

## Register Your Webhook

Once your Flask server is running and exposed via ngrok, register the webhook so Telegram knows where to send messages:

```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook?url=https://<your-ngrok-url>/webhook"
```

Replace `<YOUR_TOKEN>` and `<your-ngrok-url>`. You should get back:

```json
{"ok":true,"result":true,"description":"Webhook was set"}
```

## Verify the Webhook is Set

```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo"
```

---

## Tips

- **Keep your token secret** — anyone with it can control your bot
- **Never commit `.env` to git** — it's already in `.gitignore`
- If you leak the token, revoke it immediately: send `/revoke` to BotFather
- To find your bot later: BotFather → `/mybots` → select your bot → API Token
