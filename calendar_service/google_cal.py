from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import sqlite3

from google.oauth2 import service_account
from googleapiclient.discovery import build

import config

_SCOPES = ["https://www.googleapis.com/auth/calendar"]
_TZ = "Asia/Kolkata"


def _service():
    creds = service_account.Credentials.from_service_account_file(
        config.GOOGLE_SERVICE_ACCOUNT_FILE, scopes=_SCOPES
    )
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def check_availability(slot_iso: str) -> bool:
    """Return True if the slot is free, False if busy."""
    tz = ZoneInfo(_TZ)
    start = datetime.fromisoformat(slot_iso).replace(tzinfo=tz)
    end = start + timedelta(minutes=config.APPOINTMENT_DURATION_MINUTES)

    body = {
        "timeMin": start.isoformat(),
        "timeMax": end.isoformat(),
        "timeZone": _TZ,
        "items": [{"id": config.GOOGLE_CALENDAR_ID}],
    }
    result = _service().freebusy().query(body=body).execute()
    busy = result["calendars"][config.GOOGLE_CALENDAR_ID]["busy"]
    return len(busy) == 0


def create_event(name: str, telegram_user: str | None, slot_iso: str) -> str:
    """Create a calendar event and return the event ID."""
    tz = ZoneInfo(_TZ)
    start = datetime.fromisoformat(slot_iso).replace(tzinfo=tz)
    end = start + timedelta(minutes=config.APPOINTMENT_DURATION_MINUTES)

    contact = f"@{telegram_user}" if telegram_user else "Telegram user"
    event = {
        "summary": f"Appointment — {name}",
        "description": f"Booked via Telegram bot\nContact: {contact}",
        "start": {"dateTime": start.isoformat(), "timeZone": _TZ},
        "end": {"dateTime": end.isoformat(), "timeZone": _TZ},
    }
    created = _service().events().insert(
        calendarId=config.GOOGLE_CALENDAR_ID, body=event
    ).execute()
    return created["id"]


def next_available_slot(from_iso: str, days_ahead: int = 7) -> str | None:
    """Find the next free slot starting from from_iso within days_ahead days."""
    tz = ZoneInfo(_TZ)
    start = datetime.fromisoformat(from_iso).replace(tzinfo=tz)
    duration = timedelta(minutes=config.APPOINTMENT_DURATION_MINUTES)
    step = timedelta(hours=1)
    end_search = start + timedelta(days=days_ahead)

    svc = _service()
    body = {
        "timeMin": start.isoformat(),
        "timeMax": end_search.isoformat(),
        "timeZone": _TZ,
        "items": [{"id": config.GOOGLE_CALENDAR_ID}],
    }
    result = svc.freebusy().query(body=body).execute()
    busy_blocks = result["calendars"][config.GOOGLE_CALENDAR_ID]["busy"]

    # Walk hour by hour within business hours (9am–5pm)
    candidate = start
    while candidate < end_search:
        hour = candidate.hour
        if 9 <= hour < 17:  # within business hours
            slot_end = candidate + duration
            conflict = any(
                datetime.fromisoformat(b["start"]).replace(tzinfo=tz) < slot_end
                and datetime.fromisoformat(b["end"]).replace(tzinfo=tz) > candidate
                for b in busy_blocks
            )
            if not conflict:
                return candidate.strftime("%Y-%m-%dT%H:%M:%S")
        candidate += step

    return None
