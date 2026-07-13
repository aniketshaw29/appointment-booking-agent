"""Custom exceptions and user-facing error messages for the booking bot."""

import logging
import traceback

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("booking_bot")


class GeminiError(Exception):
    """Raised when the Gemini API call fails."""
    pass


class GeminiQuotaError(GeminiError):
    """Raised when the Gemini free-tier quota is exhausted."""
    pass


class CalendarError(Exception):
    """Raised when a Google Calendar API call fails."""
    pass


class CalendarAuthError(CalendarError):
    """Raised when service account credentials are invalid or missing."""
    pass


class BookingConflictError(Exception):
    """Raised when a slot is already booked."""
    pass


# User-facing messages — what we send back to the person on Telegram
MESSAGES = {
    "gemini_quota": (
        "I'm getting a lot of requests right now and hit my AI limit. "
        "Please try again in a few minutes. 🙏"
    ),
    "gemini_error": (
        "I'm having trouble thinking right now. "
        "Please send /start and try again."
    ),
    "calendar_auth": (
        "There's a configuration issue on my end — I can't access the calendar. "
        "Please contact the business directly."
    ),
    "calendar_error": (
        "I couldn't reach the calendar right now. "
        "Please try again in a moment."
    ),
    "no_slots": (
        "I couldn't find any free slots in the next 7 days. "
        "Please try a different date or contact us directly."
    ),
    "booking_failed": (
        "I confirmed the slot but couldn't save the booking. "
        "Please screenshot this and contact the business to confirm."
    ),
    "slot_in_past": (
        "That date has already passed! "
        "Please pick a future date and time."
    ),
    "outside_hours": (
        "That time is outside our business hours ({hours}). "
        "Please pick a time within those hours."
    ),
    "unknown": (
        "Something unexpected happened on my end. "
        "Please send /start to try again."
    ),
}


def log_error(context: str, exc: Exception) -> None:
    """Log the full traceback for debugging without exposing it to the user."""
    logger.error("%s: %s\n%s", context, exc, traceback.format_exc())
