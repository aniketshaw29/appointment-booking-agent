# Testing Guide

Run the full test suite anytime to verify nothing is broken:

```bash
.venv/bin/python -m pytest tests/ -v
```

Expected output: **36 passed**.

---

## What's Covered

### DB Layer (`TestDB` — 8 tests)

| Test | What it checks |
|---|---|
| `test_init_creates_tables` | `sessions` and `bookings` tables exist after `init_db()` |
| `test_get_or_create_session_new` | New chat gets correct defaults (`state=COLLECT_NAME`, all fields `None`) |
| `test_get_or_create_session_idempotent` | Calling twice for same `chat_id` returns same session |
| `test_save_session_persists_fields` | name, age, location, nature, purpose, proposed_slot all saved correctly |
| `test_create_booking_returns_id` | Returns positive integer row ID on first insert |
| `test_create_booking_idempotent` | Duplicate insert returns `0` (UNIQUE constraint, `INSERT OR IGNORE`) |
| `test_get_bookings_in_range` | Returns only bookings within the date range |
| `test_migration_adds_missing_columns` | Running `init_db()` on old-schema DB adds missing columns without crashing |

### Schema (`TestAgentResponse` — 4 tests)

| Test | What it checks |
|---|---|
| `test_valid_clarify` | Basic AgentResponse with optional fields as `None` |
| `test_all_fields` | All 8 fields populated correctly |
| `test_invalid_action_raises` | Pydantic raises `ValidationError` on unknown action |
| `test_valid_actions` | All 4 valid actions accepted: `clarify`, `check_availability`, `book`, `done` |

### LLM Layer (`TestLLM` — 4 tests)

| Test | What it checks |
|---|---|
| `test_get_available_models_returns_all` | All 4 models present: Gemini 2.5, Gemini 2.0, GPT-4o-mini, GPT-4o |
| `test_models_have_required_keys` | Each model has `id`, `label`, `provider` |
| `test_all_models_have_known_provider` | Provider is `gemini` or `openai` only |
| `test_reset_chat_does_not_crash` | `reset_chat()` handles unknown `chat_id` gracefully |

### Flask App (`TestFlaskApp` — 16 tests)

| Test | What it checks |
|---|---|
| `test_health` | `GET /health` returns 200 with `status`, `business`, `model` |
| `test_landing_page` | `GET /` returns 200 with business name in HTML |
| `test_webhook_bad_body_graceful` | Non-JSON POST to `/webhook` returns `{"ok": true}` without crash |
| `test_webhook_start_command` | `/start` sends greeting containing business name |
| `test_webhook_cancel_command` | `/cancel` sends cancellation message |
| `test_webhook_help_command` | `/help` sends a reply |
| `test_webhook_secret_wrong_rejected` | Wrong secret header returns 403 |
| `test_webhook_secret_correct_accepted` | Correct secret header returns 200 |
| `test_gemini_quota_error_sends_friendly_message` | `GeminiQuotaError` → user gets "a lot of requests" message |
| `test_gemini_error_sends_friendly_message` | `GeminiError` → user gets "having trouble" message |
| `test_admin_login_page_shown_when_not_logged_in` | `GET /admin` without session shows login page |
| `test_admin_login_wrong_password` | Wrong password shows error, stays on login |
| `test_admin_login_correct_password_redirects` | Correct password → redirects to admin dashboard |
| `test_admin_set_model_requires_login` | POST to `/admin/set-model` without login → 403 |
| `test_admin_set_model_switches_model` | Logged-in admin can switch to `gpt-4o-mini` — `/health` reflects new model |
| `test_admin_set_model_invalid_rejected` | Unknown model ID → rejected, active model unchanged |

### Error Module (`TestErrors` — 4 tests)

| Test | What it checks |
|---|---|
| `test_gemini_quota_is_subclass_of_gemini_error` | `GeminiQuotaError` inherits from `GeminiError` (catchable as parent) |
| `test_calendar_auth_is_subclass_of_calendar_error` | Same pattern for calendar errors |
| `test_all_message_keys_present` | All 8 user-facing message keys exist in `MESSAGES` dict |
| `test_messages_are_non_empty_strings` | No empty or placeholder messages |

---

## Running Specific Tests

```bash
# Run a single test class
.venv/bin/python -m pytest tests/test_app.py::TestDB -v

# Run a single test
.venv/bin/python -m pytest tests/test_app.py::TestFlaskApp::test_health -v

# Run with output (print statements visible)
.venv/bin/python -m pytest tests/test_app.py -v -s

# Run and stop on first failure
.venv/bin/python -m pytest tests/test_app.py -x
```

## What's NOT Covered (requires live credentials)

| Feature | Why not tested |
|---|---|
| Gemini / OpenAI real API calls | Need live keys + quota |
| Google Calendar freebusy | Need service account + live calendar |
| Telegram `sendMessage` | Need real bot token + chat ID |
| Full booking flow end-to-end | Requires all of the above |

For end-to-end testing, run the bot locally with ngrok and test manually via Telegram.

## Adding New Tests

When adding a feature, add a test in `tests/test_app.py` in the appropriate class. Keep the pattern:

```python
def test_my_new_feature(self):
    with mock.patch("app.send_message") as ms:
        r = self.client().post("/webhook", json={
            "message": {"chat": {"id": 1}, "from": {"username": "u"}, "text": "your input"}
        })
        self.assertEqual(r.status_code, 200)
        # assert on ms.call_args[0][1] for the reply text
```
