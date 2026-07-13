"""
Unit + integration tests for the appointment booking bot.
Run with: .venv/bin/python -m pytest tests/ -v
No live API calls — Gemini and Telegram are fully mocked.
"""
import os
import sys
import json
import sqlite3
import tempfile
import unittest
import unittest.mock as mock

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Stub env vars before importing any app code
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "123:TEST")
os.environ.setdefault("GEMINI_API_KEY", "TEST_GEMINI")
os.environ.setdefault("OPENAI_API_KEY", "")
os.environ.setdefault("GOOGLE_SERVICE_ACCOUNT_FILE", "credentials/service_account.json")
os.environ.setdefault("GOOGLE_CALENDAR_ID", "test@calendar.google.com")
os.environ.setdefault("BUSINESS_NAME", "Test Clinic")
os.environ.setdefault("BUSINESS_HOURS", "Monday-Friday, 9am-5pm")
os.environ.setdefault("APPOINTMENT_DURATION_MINUTES", "30")
os.environ.setdefault("ADMIN_PASSWORD", "testpass123")
os.environ.setdefault("ACTIVE_MODEL", "gemini-2.5-flash")
os.environ.setdefault("TELEGRAM_WEBHOOK_SECRET", "")


# ── DB tests ──────────────────────────────────────────────────────────────────

import calendar_service.db as db


class TestDB(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mktemp(suffix=".db")
        db.DB_PATH = self.tmp
        db.init_db()

    def tearDown(self):
        try:
            os.unlink(self.tmp)
        except FileNotFoundError:
            pass

    def test_init_creates_tables(self):
        con = sqlite3.connect(self.tmp)
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        self.assertIn("sessions", tables)
        self.assertIn("bookings", tables)
        con.close()

    def test_get_or_create_session_new(self):
        s = db.get_or_create_session(1001)
        self.assertEqual(s["chat_id"], 1001)
        self.assertEqual(s["state"], "COLLECT_NAME")
        self.assertIsNone(s["name"])

    def test_get_or_create_session_idempotent(self):
        db.get_or_create_session(1002)
        s2 = db.get_or_create_session(1002)
        self.assertEqual(s2["chat_id"], 1002)

    def test_save_session_persists_fields(self):
        db.save_session(1003, [{"role": "user", "content": "hi"}],
                        "CHECK_AVAILABILITY", name="Ravi", age="28",
                        location="Bangalore", nature="business",
                        purpose="demo", proposed_slot="2026-08-01T10:00:00")
        s = db.get_or_create_session(1003)
        self.assertEqual(s["name"], "Ravi")
        self.assertEqual(s["age"], "28")
        self.assertEqual(s["location"], "Bangalore")
        self.assertEqual(s["proposed_slot"], "2026-08-01T10:00:00")

    def test_create_booking_returns_id(self):
        row_id = db.create_booking(1004, "Priya", "priya_tg", "2026-08-01T10:00:00", "evt1")
        self.assertGreater(row_id, 0)

    def test_create_booking_idempotent(self):
        db.create_booking(1005, "Ravi", "ravi_tg", "2026-08-02T11:00:00", "evt2")
        id2 = db.create_booking(1005, "Ravi", "ravi_tg", "2026-08-02T11:00:00", "evt2")
        self.assertEqual(id2, 0)  # INSERT OR IGNORE

    def test_get_bookings_in_range(self):
        db.create_booking(1006, "Alice", None, "2026-08-10T09:00:00")
        db.create_booking(1006, "Bob",   None, "2026-08-11T09:00:00")
        rows = db.get_bookings_in_range("2026-08-09T00:00:00", "2026-08-12T00:00:00")
        self.assertEqual(len(rows), 2)
        self.assertEqual({r["name"] for r in rows}, {"Alice", "Bob"})

    def test_migration_adds_missing_columns(self):
        """init_db() on an old-schema DB should add new columns without crashing."""
        con = sqlite3.connect(self.tmp)
        # Drop the age column by recreating a stripped table
        con.execute("CREATE TABLE IF NOT EXISTS sessions_old AS SELECT chat_id, history, state FROM sessions")
        con.execute("DROP TABLE sessions")
        con.execute("ALTER TABLE sessions_old RENAME TO sessions")
        con.commit()
        con.close()
        # Running init_db again should migrate without error
        db.init_db()
        con2 = sqlite3.connect(self.tmp)
        cols = {row[1] for row in con2.execute("PRAGMA table_info(sessions)")}
        self.assertIn("age", cols)
        self.assertIn("nature", cols)
        con2.close()


# ── Schema tests ──────────────────────────────────────────────────────────────

from agent.schemas import AgentResponse
from pydantic import ValidationError


class TestAgentResponse(unittest.TestCase):

    def test_valid_clarify(self):
        r = AgentResponse(reply_text="Hi!", action="clarify", extracted_name="Ravi")
        self.assertEqual(r.action, "clarify")
        self.assertEqual(r.extracted_name, "Ravi")
        self.assertIsNone(r.proposed_slot)

    def test_all_fields(self):
        r = AgentResponse(
            reply_text="ok",
            action="check_availability",
            extracted_name="Ravi",
            extracted_age="28",
            extracted_location="Bangalore",
            extracted_nature="business",
            extracted_purpose="demo",
            proposed_slot="2026-08-01T10:00:00"
        )
        self.assertEqual(r.extracted_nature, "business")
        self.assertEqual(r.proposed_slot, "2026-08-01T10:00:00")

    def test_invalid_action_raises(self):
        with self.assertRaises(ValidationError):
            AgentResponse(reply_text="hi", action="INVALID")

    def test_valid_actions(self):
        for action in ["clarify", "check_availability", "book", "done"]:
            r = AgentResponse(reply_text="x", action=action)
            self.assertEqual(r.action, action)


# ── LLM layer tests ───────────────────────────────────────────────────────────

from agent.llm import get_available_models, ALL_MODELS, reset_chat as llm_reset


class TestLLM(unittest.TestCase):

    def test_get_available_models_returns_all(self):
        models = get_available_models()
        ids = {m["id"] for m in models}
        self.assertIn("gemini-2.5-flash", ids)
        self.assertIn("gpt-4o-mini", ids)
        self.assertIn("gpt-4o", ids)

    def test_models_have_required_keys(self):
        for m in get_available_models():
            self.assertIn("id", m)
            self.assertIn("label", m)
            self.assertIn("provider", m)

    def test_all_models_have_known_provider(self):
        for k, v in ALL_MODELS.items():
            self.assertIn(v["provider"], ["gemini", "openai"], f"{k} has unknown provider")

    def test_reset_chat_does_not_crash(self):
        llm_reset(99999)  # should not raise even for unknown chat_id


# ── Flask app tests ───────────────────────────────────────────────────────────

class TestFlaskApp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mktemp(suffix=".db")
        db.DB_PATH = cls.tmp
        with mock.patch("google.generativeai.configure"), \
             mock.patch("google.generativeai.GenerativeModel"):
            import app as flask_app
            flask_app.app.config["TESTING"] = True
            flask_app.app.config["SECRET_KEY"] = "testkey"
            cls.app = flask_app.app
            cls.flask_app = flask_app

    @classmethod
    def tearDownClass(cls):
        try:
            os.unlink(cls.tmp)
        except FileNotFoundError:
            pass

    def client(self):
        return self.app.test_client()

    def test_health(self):
        r = self.client().get("/health")
        self.assertEqual(r.status_code, 200)
        d = r.get_json()
        self.assertEqual(d["status"], "ok")
        self.assertEqual(d["business"], "Test Clinic")
        self.assertIn("model", d)

    def test_landing_page(self):
        r = self.client().get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Test Clinic", r.data)

    def test_webhook_bad_body_graceful(self):
        r = self.client().post("/webhook", data="notjson", content_type="text/plain")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["ok"])

    def test_webhook_start_command(self):
        with mock.patch("app.send_message") as ms:
            r = self.client().post("/webhook", json={
                "message": {"chat": {"id": 1}, "from": {"username": "u"}, "text": "/start"}
            })
            self.assertEqual(r.status_code, 200)
            self.assertTrue(ms.called)
            self.assertIn("Test Clinic", ms.call_args[0][1])

    def test_webhook_cancel_command(self):
        with mock.patch("app.send_message") as ms:
            r = self.client().post("/webhook", json={
                "message": {"chat": {"id": 1}, "from": {"username": "u"}, "text": "/cancel"}
            })
            self.assertEqual(r.status_code, 200)
            self.assertTrue(ms.called)
            msg = ms.call_args[0][1].lower()
            self.assertTrue("cancel" in msg or "start" in msg)

    def test_webhook_help_command(self):
        with mock.patch("app.send_message") as ms:
            r = self.client().post("/webhook", json={
                "message": {"chat": {"id": 1}, "from": {"username": "u"}, "text": "/help"}
            })
            self.assertEqual(r.status_code, 200)
            self.assertTrue(ms.called)

    def test_webhook_secret_wrong_rejected(self):
        import config as cfg
        cfg.TELEGRAM_WEBHOOK_SECRET = "secret123"
        r = self.client().post("/webhook", json={
            "message": {"chat": {"id": 1}, "from": {"username": "u"}, "text": "hi"}
        })
        self.assertEqual(r.status_code, 403)
        cfg.TELEGRAM_WEBHOOK_SECRET = ""

    def test_webhook_secret_correct_accepted(self):
        import config as cfg
        cfg.TELEGRAM_WEBHOOK_SECRET = "secret123"
        with mock.patch("app.send_message"), mock.patch("app.process_turn") as mt:
            mt.return_value = AgentResponse(reply_text="Hi!", action="clarify")
            r = self.client().post("/webhook",
                json={"message": {"chat": {"id": 2}, "from": {"username": "u"}, "text": "hi"}},
                headers={"X-Telegram-Bot-Api-Secret-Token": "secret123"}
            )
            self.assertEqual(r.status_code, 200)
        cfg.TELEGRAM_WEBHOOK_SECRET = ""

    def test_gemini_quota_error_sends_friendly_message(self):
        from errors import GeminiQuotaError, MESSAGES
        with mock.patch("app.process_turn", side_effect=GeminiQuotaError("quota")), \
             mock.patch("app.send_message") as ms:
            r = self.client().post("/webhook", json={
                "message": {"chat": {"id": 3}, "from": {"username": "u"}, "text": "hello"}
            })
            self.assertEqual(r.status_code, 200)
            self.assertIn(MESSAGES["gemini_quota"][:20], ms.call_args[0][1])

    def test_gemini_error_sends_friendly_message(self):
        from errors import GeminiError, MESSAGES
        with mock.patch("app.process_turn", side_effect=GeminiError("fail")), \
             mock.patch("app.send_message") as ms:
            r = self.client().post("/webhook", json={
                "message": {"chat": {"id": 4}, "from": {"username": "u"}, "text": "hello"}
            })
            self.assertEqual(r.status_code, 200)
            self.assertIn(MESSAGES["gemini_error"][:20], ms.call_args[0][1])

    def test_admin_login_page_shown_when_not_logged_in(self):
        r = self.client().get("/admin")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Admin Login", r.data)

    def test_admin_login_wrong_password(self):
        r = self.client().post("/admin/login", data={"password": "wrong"})
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Incorrect", r.data)

    def test_admin_login_correct_password_redirects(self):
        r = self.client().post("/admin/login", data={"password": "testpass123"},
                               follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Admin Panel", r.data)

    def test_admin_set_model_requires_login(self):
        r = self.client().post("/admin/set-model", data={"model_id": "gpt-4o-mini"})
        self.assertEqual(r.status_code, 403)

    def test_admin_set_model_switches_model(self):
        client = self.client()
        client.post("/admin/login", data={"password": "testpass123"})
        client.post("/admin/set-model", data={"model_id": "gpt-4o-mini"}, follow_redirects=True)
        r = client.get("/health")
        d = r.get_json()
        self.assertEqual(d["model"], "gpt-4o-mini")
        # Reset back
        client.post("/admin/set-model", data={"model_id": "gemini-2.5-flash"})

    def test_admin_set_model_invalid_rejected(self):
        client = self.client()
        # Login first
        client.post("/admin/login", data={"password": "testpass123"})
        # Try an invalid model — should stay on admin page (200) and not crash
        r = client.post("/admin/set-model", data={"model_id": "fake-model-99"},
                        follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        # Model should not have changed to the invalid one
        r2 = client.get("/health")
        self.assertNotEqual(r2.get_json()["model"], "fake-model-99")


# ── Error module tests ────────────────────────────────────────────────────────

from errors import GeminiError, GeminiQuotaError, CalendarError, CalendarAuthError, MESSAGES


class TestErrors(unittest.TestCase):

    def test_gemini_quota_is_subclass_of_gemini_error(self):
        self.assertTrue(issubclass(GeminiQuotaError, GeminiError))

    def test_calendar_auth_is_subclass_of_calendar_error(self):
        self.assertTrue(issubclass(CalendarAuthError, CalendarError))

    def test_all_message_keys_present(self):
        for key in ["gemini_quota", "gemini_error", "calendar_auth", "calendar_error",
                    "no_slots", "booking_failed", "slot_in_past", "unknown"]:
            self.assertIn(key, MESSAGES, f"Missing message key: {key}")

    def test_messages_are_non_empty_strings(self):
        for key, msg in MESSAGES.items():
            self.assertIsInstance(msg, str)
            self.assertGreater(len(msg), 10, f"Message too short for key: {key}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
