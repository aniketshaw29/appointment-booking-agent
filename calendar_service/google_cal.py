from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from google.oauth2 import service_account
from google.auth.exceptions import DefaultCredentialsError, TransportError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import config
from errors import CalendarError, CalendarAuthError, BookingConflictError, log_error

_SCOPES = ["https://www.googleapis.com/auth/calendar"]
_TZ = "Asia/Kolkata"


def _service():
    try:
        creds = service_account.Credentials.from_service_account_file(
            config.GOOGLE_SERVICE_ACCOUNT_FILE, scopes=_SCOPES
        )
        return build("calendar", "v3", credentials=creds, cache_discovery=False)
    except (FileNotFoundError, ValueError, DefaultCredentialsError) as e:
        log_error("Calendar auth failed", e)
        raise CalendarAuthError(f"Service account error: {e}") from e


def _validate_slot(slot_iso: str) -> datetime:
    """Parse slot and raise CalendarError if it's in the past."""
    tz = ZoneInfo(_TZ)
    try:
        dt = datetime.fromisoformat(slot_iso).replace(tzinfo=tz)
    except ValueError as e:
        raise CalendarError(f"Invalid slot format: {slot_iso}") from e

    if dt < datetime.now(tz):
        raise BookingConflictError("slot_in_past")
    return dt


def check_availability(slot_iso: str) -> bool:
    """Return True if the slot is free, False if busy. Raises CalendarError on failure."""
    tz = ZoneInfo(_TZ)
    start = _validate_slot(slot_iso)
    end = start + timedelta(minutes=config.APPOINTMENT_DURATION_MINUTES)

    body = {
        "timeMin": start.isoformat(),
        "timeMax": end.isoformat(),
        "timeZone": _TZ,
        "items": [{"id": config.GOOGLE_CALENDAR_ID}],
    }
    try:
        result = _service().freebusy().query(body=body).execute()
        busy = result["calendars"][config.GOOGLE_CALENDAR_ID]["busy"]
        return len(busy) == 0
    except CalendarAuthError:
        raise
    except HttpError as e:
        log_error("Calendar freebusy HTTP error", e)
        raise CalendarError(f"Calendar API HTTP error: {e.status_code}") from e
    except Exception as e:
        log_error("Calendar freebusy unexpected error", e)
        raise CalendarError(f"Calendar unavailable: {e}") from e


def create_event(name: str, telegram_user: str | None, slot_iso: str,
                 age: str | None = None, location: str | None = None,
                 nature: str | None = None, purpose: str | None = None) -> str:
    """Create a calendar event and return the event ID."""
    tz = ZoneInfo(_TZ)
    start = _validate_slot(slot_iso)
    end = start + timedelta(minutes=config.APPOINTMENT_DURATION_MINUTES)

    contact = f"@{telegram_user}" if telegram_user else "Telegram user"
    lines = ["Booked via Telegram bot", f"Contact: {contact}"]
    if age:      lines.append(f"Age: {age}")
    if location: lines.append(f"Location: {location}")
    if nature:   lines.append(f"Nature: {nature.capitalize()}")
    if purpose:  lines.append(f"Purpose: {purpose}")

    event = {
        "summary": f"Appointment — {name}",
        "description": "\n".join(lines),
        "start": {"dateTime": start.isoformat(), "timeZone": _TZ},
        "end": {"dateTime": end.isoformat(), "timeZone": _TZ},
    }
    try:
        created = _service().events().insert(
            calendarId=config.GOOGLE_CALENDAR_ID, body=event
        ).execute()
        return created["id"]
    except CalendarAuthError:
        raise
    except HttpError as e:
        log_error("Calendar create_event HTTP error", e)
        raise CalendarError(f"Failed to create event: {e.status_code}") from e
    except Exception as e:
        log_error("Calendar create_event unexpected error", e)
        raise CalendarError(f"Event creation failed: {e}") from e


def next_available_slot(from_iso: str, days_ahead: int = 7) -> str | None:
    """Find the next free slot within days_ahead days. Returns None if nothing found."""
    tz = ZoneInfo(_TZ)
    try:
        start = datetime.fromisoformat(from_iso).replace(tzinfo=tz)
    except ValueError:
        return None

    duration = timedelta(minutes=config.APPOINTMENT_DURATION_MINUTES)
    step = timedelta(hours=1)
    end_search = start + timedelta(days=days_ahead)

    try:
        svc = _service()
        body = {
            "timeMin": start.isoformat(),
            "timeMax": end_search.isoformat(),
            "timeZone": _TZ,
            "items": [{"id": config.GOOGLE_CALENDAR_ID}],
        }
        result = svc.freebusy().query(body=body).execute()
        busy_blocks = result["calendars"][config.GOOGLE_CALENDAR_ID]["busy"]
    except Exception as e:
        log_error("next_available_slot freebusy failed", e)
        return None

    candidate = start
    while candidate < end_search:
        if 9 <= candidate.hour < 17:
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
