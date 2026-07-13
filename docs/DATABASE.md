# Database

SQLite is used as the database — zero-ops, no server, file-based. The DB file (`bookings.db`) lives in the project root and is created automatically on first startup.

---

## Tables

### `sessions`

Tracks one row per Telegram user. Stores the full conversation state so the bot remembers what has already been collected between messages.

```sql
CREATE TABLE sessions (
    chat_id       INTEGER PRIMARY KEY,       -- Telegram chat ID (unique per user)
    history       TEXT    NOT NULL DEFAULT '[]',  -- JSON array of {role, content} turns
    state         TEXT    NOT NULL DEFAULT 'COLLECT_NAME',  -- current dialog state
    name          TEXT,                      -- extracted name
    age           TEXT,                      -- extracted age
    location      TEXT,                      -- extracted city/area
    nature        TEXT,                      -- work | business | casual | other
    purpose       TEXT,                      -- free-text purpose of meeting
    proposed_slot TEXT,                      -- ISO8601 datetime being discussed
    updated_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);
```

**State values:** `COLLECT_NAME` → `COLLECT_DATETIME` → `CHECK_AVAILABILITY` → `CONFIRM_BOOKING` → `BOOK_AND_END` (and `CLARIFY`, `DONE`)

**`history` field:** Full Gemini/OpenAI message history as JSON, e.g.:
```json
[
  {"role": "user", "content": "I'm Ravi"},
  {"role": "assistant", "content": "Nice to meet you, Ravi! ..."}
]
```
This is passed back to the LLM on every turn so it maintains conversational context.

---

### `bookings`

One row per confirmed appointment.

```sql
CREATE TABLE bookings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id         INTEGER NOT NULL,        -- Telegram chat ID of the person who booked
    name            TEXT    NOT NULL,        -- Collected name
    age             TEXT,                    -- Collected age
    location        TEXT,                    -- Collected location
    nature          TEXT,                    -- work | business | casual | other
    purpose         TEXT,                    -- Purpose of meeting
    telegram_user   TEXT,                    -- @username if available
    slot_dt         TEXT    NOT NULL,        -- ISO8601 appointment datetime
    google_event_id TEXT,                    -- Google Calendar event ID
    status          TEXT    NOT NULL DEFAULT 'confirmed',
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(name, slot_dt)                    -- prevents duplicate bookings
);
```

**`UNIQUE(name, slot_dt)`** — if the same person tries to book the same slot twice (e.g. Telegram retries the webhook), the second insert is silently ignored (`INSERT OR IGNORE`). This ensures idempotency.

---

## Key Functions (`calendar_service/db.py`)

### Session management

```python
get_or_create_session(chat_id: int) -> dict
```
Returns existing session or creates a new one with defaults. Called at the start of every webhook request.

```python
save_session(chat_id, history, state, name, age, location, nature, purpose, proposed_slot)
```
Upserts the session row (`INSERT ... ON CONFLICT DO UPDATE`). Called at the end of every webhook request.

### Booking

```python
create_booking(chat_id, name, telegram_user, slot_dt, google_event_id, age, location, nature, purpose) -> int
```
Returns the new row ID, or `0` if the booking already exists (idempotent).

```python
get_bookings_in_range(start: str, end: str) -> list[dict]
```
Returns all confirmed bookings in the given ISO8601 date range. Used for availability checks.

---

## Migrations

`init_db()` is called on every app startup. It:
1. Creates tables if they don't exist (`CREATE TABLE IF NOT EXISTS`)
2. Runs `ALTER TABLE` migrations to add any columns that are missing from an older schema

This means you can deploy a new version with new columns and the existing DB upgrades automatically — no manual SQL needed.

```python
def _add_column_if_missing(con, table, column, col_type):
    existing = {row[1] for row in con.execute(f"PRAGMA table_info({table})")}
    if column not in existing:
        con.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
```

---

## Querying the DB Directly

```bash
# View all bookings
sqlite3 bookings.db "SELECT id, name, slot_dt, nature, purpose FROM bookings ORDER BY slot_dt"

# View all sessions
sqlite3 bookings.db "SELECT chat_id, state, name, proposed_slot FROM sessions"

# Count bookings by nature
sqlite3 bookings.db "SELECT nature, COUNT(*) FROM bookings GROUP BY nature"
```

---

## Production Considerations

- **SQLite resets on Render redeploy** — the DB file is ephemeral on Render's free tier. All bookings are lost when the service restarts. For production, switch to Render's managed Postgres (free tier available).
- **No concurrent writes issue** — SQLite handles one writer at a time. With one Gunicorn worker (Render free tier), this is fine. If you scale to multiple workers, switch to Postgres.
- **Backup** — for a personal project, export periodically: `sqlite3 bookings.db .dump > backup.sql`
