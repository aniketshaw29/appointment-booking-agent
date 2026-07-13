# Google Calendar API Setup

This guide sets up the Google Calendar integration for the appointment booking bot.

---

## Step 1 — Enable the Google Calendar API

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your project: **Aniket Appointment booking app**
3. In the left menu → **APIs & Services** → **Library**
4. Search for **Google Calendar API**
5. Click it → click **Enable**

---

## Step 2 — Create a Service Account

1. Left menu → **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** → **Service Account**
3. Fill in:
   - **Service account name:** `aniket-appointment-bot` (or any name)
   - Click **Create and Continue**
4. **Role:** select **Editor**
5. Click **Continue** → **Done**

---

## Step 3 — Download the JSON Key

1. On the Credentials page, find your service account under **Service Accounts**
2. Click on it → go to the **Keys** tab
3. Click **Add Key** → **Create new key** → choose **JSON**
4. The file downloads automatically — rename it to `service_account.json`
5. Move it to `credentials/service_account.json` in the project root

> ⚠️ **Never commit this file.** It's already in `.gitignore`.

Your service account email will look like:
```
aniket-appointment-bot@aniket-appointment-booking-app.iam.gserviceaccount.com
```

---

## Step 4 — Share Your Google Calendar with the Service Account

The bot needs permission to read/write your calendar.

1. Open [Google Calendar](https://calendar.google.com)
2. On the left sidebar, find the calendar you want to use → click the **⋮** menu → **Settings and sharing**
3. Scroll down to **Share with specific people or groups**
4. Click **+ Add people**
5. Enter the service account email:
   ```
   aniket-appointment-bot@aniket-appointment-booking-app.iam.gserviceaccount.com
   ```
6. Set permission to **Make changes to events**
7. Click **Send**

---

## Step 5 — Get Your Calendar ID

1. In Google Calendar → Settings for your calendar
2. Scroll down to **Integrate calendar**
3. Copy the **Calendar ID** — it looks like:
   - Your primary calendar: `your.email@gmail.com`
   - A separate calendar: `abc123xyz@group.calendar.google.com`

---

## Step 6 — Update Your .env File

```bash
GOOGLE_SERVICE_ACCOUNT_FILE=credentials/service_account.json
GOOGLE_CALENDAR_ID=your-calendar-id-here
```

---

## Verify It's Working

Run this quick test to confirm the credentials work:

```bash
python - << 'EOF'
import os
os.environ["GOOGLE_SERVICE_ACCOUNT_FILE"] = "credentials/service_account.json"
os.environ["GOOGLE_CALENDAR_ID"] = "your-calendar-id"

from google.oauth2 import service_account
from googleapiclient.discovery import build

creds = service_account.Credentials.from_service_account_file(
    "credentials/service_account.json",
    scopes=["https://www.googleapis.com/auth/calendar"]
)
service = build("calendar", "v3", credentials=creds)
cal = service.calendars().get(calendarId=os.environ["GOOGLE_CALENDAR_ID"]).execute()
print(f"✅ Connected to calendar: {cal['summary']}")
EOF
```

If you see `✅ Connected to calendar: ...` you're all set.
