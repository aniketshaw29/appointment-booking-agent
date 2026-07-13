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
GOOGLE_CALENDAR_ID = _require("GOOGLE_CALENDAR_ID")

# Local dev: set GOOGLE_SERVICE_ACCOUNT_FILE=credentials/service_account.json in .env
# Render: add as Secret File with filename "service_account.json" — it lands at /etc/secrets/service_account.json
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv(
    "GOOGLE_SERVICE_ACCOUNT_FILE",
    "/etc/secrets/service_account.json"
)

BUSINESS_NAME = os.getenv("BUSINESS_NAME", "Our Business")
BUSINESS_HOURS = os.getenv("BUSINESS_HOURS", "Monday-Friday, 9am-5pm")
_raw_duration = int(os.getenv("APPOINTMENT_DURATION_MINUTES", "30"))
APPOINTMENT_DURATION_MINUTES = min(_raw_duration, 30)

TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")

# OpenAI — optional, only needed if using GPT models
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Admin panel password — set via ADMIN_PASSWORD env var
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Active AI model — can be changed at runtime via /admin
# Options: gemini-2.5-flash, gemini-2.0-flash, gpt-4o-mini, gpt-4o
ACTIVE_MODEL = os.getenv("ACTIVE_MODEL", "gemini-2.5-flash")
