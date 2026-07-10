import os
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


TELEGRAM_BOT_TOKEN = _require("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = _require("GEMINI_API_KEY")
GOOGLE_SERVICE_ACCOUNT_FILE = _require("GOOGLE_SERVICE_ACCOUNT_FILE")
GOOGLE_CALENDAR_ID = _require("GOOGLE_CALENDAR_ID")

BUSINESS_NAME = os.getenv("BUSINESS_NAME", "Our Business")
BUSINESS_HOURS = os.getenv("BUSINESS_HOURS", "Monday-Friday, 9am-5pm")
APPOINTMENT_DURATION_MINUTES = int(os.getenv("APPOINTMENT_DURATION_MINUTES", "60"))
