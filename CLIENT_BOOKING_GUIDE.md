# How Clients Can Start a Booking

Anyone can book an appointment by messaging the bot on Telegram. No signup or login needed.

---

## Option 1 — Direct Link (Easiest)

Share this link with clients — tapping it opens a chat with the bot instantly:

```
https://t.me/aniketshaw_appointment_bot
```

They tap **Start** and the bot greets them automatically.

---

## Option 2 — Search in Telegram

1. Open Telegram
2. Tap the search icon
3. Search: `@aniketshaw_appointment_bot`
4. Tap the bot → tap **Start**

---

## Option 3 — QR Code

Generate a QR code for `https://t.me/aniketshaw_appointment_bot` using any free QR generator (e.g. [qr-code-generator.com](https://www.qr-code-generator.com)) and put it on:
- Your business card
- Your website
- A printed sign at your office

Clients scan it → Telegram opens → booking starts.

---

## What the Booking Flow Looks Like for a Client

```
Client: /start  (or just send any message)

Bot: Hi! I can help you book an appointment. What's your name?

Client: I'm Priya

Bot: Nice to meet you, Priya! How old are you?

Client: 27

Bot: Where are you located?

Client: Pune

Bot: Is this for work, business, or something casual?

Client: Business

Bot: Got it! Briefly, what would you like to discuss?

Client: Partnership proposal for my startup

Bot: Great! When would you like to come in?

Client: Next Monday at 11am

Bot: Let me check... Monday, 20 July at 11:00 AM is available!
     Shall I confirm the booking for Priya? (yes/no)

Client: Yes

Bot: Done! Your appointment is confirmed for Monday, 20 July at 11:00 AM.
     A calendar invite has been created. See you then! 🎉
```

---

## Commands Clients Can Use

| Command | What it does |
|---|---|
| `/start` | Start or restart a booking |
| `/cancel` | Cancel the current booking request |

---

## Can a Client Ping/Mention You?

No — the bot works independently. Clients don't need your Telegram username or to mention you. They just message the bot directly. You see the bookings in two places:

1. **Google Calendar** — event appears automatically on confirmation
2. **SQLite database** — `bookings.db` in the project folder (or query it with `sqlite3 bookings.db "SELECT * FROM bookings"`)

---

## Sharing on WhatsApp / Instagram / Website

Add this anywhere:

> 📅 Book an appointment: [t.me/aniketshaw_appointment_bot](https://t.me/aniketshaw_appointment_bot)

Or as a button on your website:

```html
<a href="https://t.me/aniketshaw_appointment_bot" target="_blank">
  Book an Appointment on Telegram
</a>
```
