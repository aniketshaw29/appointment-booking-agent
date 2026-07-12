import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime

DB_PATH = "bookings.db"


@contextmanager
def _conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def init_db() -> None:
    with _conn() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                chat_id     INTEGER PRIMARY KEY,
                history     TEXT    NOT NULL DEFAULT '[]',
                state       TEXT    NOT NULL DEFAULT 'COLLECT_NAME',
                name        TEXT,
                proposed_slot TEXT,
                updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS bookings (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id         INTEGER NOT NULL,
                name            TEXT    NOT NULL,
                telegram_user   TEXT,
                slot_dt         TEXT    NOT NULL,
                google_event_id TEXT,
                status          TEXT    NOT NULL DEFAULT 'confirmed',
                created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
                UNIQUE(name, slot_dt)
            );
        """)


# ---------- session helpers ----------

def get_or_create_session(chat_id: int) -> dict:
    with _conn() as con:
        row = con.execute(
            "SELECT * FROM sessions WHERE chat_id = ?", (chat_id,)
        ).fetchone()
        if row:
            return dict(row)
        con.execute(
            "INSERT INTO sessions (chat_id) VALUES (?)", (chat_id,)
        )
        return {
            "chat_id": chat_id,
            "history": "[]",
            "state": "COLLECT_NAME",
            "name": None,
            "proposed_slot": None,
        }


def save_session(chat_id: int, history: list, state: str,
                 name: str | None = None, proposed_slot: str | None = None) -> None:
    with _conn() as con:
        con.execute(
            """
            INSERT INTO sessions (chat_id, history, state, name, proposed_slot, updated_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(chat_id) DO UPDATE SET
                history       = excluded.history,
                state         = excluded.state,
                name          = excluded.name,
                proposed_slot = excluded.proposed_slot,
                updated_at    = excluded.updated_at
            """,
            (chat_id, json.dumps(history), state, name, proposed_slot),
        )


# ---------- booking helpers ----------

def create_booking(chat_id: int, name: str, telegram_user: str | None,
                   slot_dt: str, google_event_id: str | None = None) -> int:
    with _conn() as con:
        cur = con.execute(
            """
            INSERT OR IGNORE INTO bookings
                (chat_id, name, telegram_user, slot_dt, google_event_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (chat_id, name, telegram_user, slot_dt, google_event_id),
        )
        return cur.lastrowid


def get_bookings_in_range(start: str, end: str) -> list[dict]:
    with _conn() as con:
        rows = con.execute(
            """
            SELECT * FROM bookings
            WHERE slot_dt >= ? AND slot_dt < ?
              AND status = 'confirmed'
            ORDER BY slot_dt
            """,
            (start, end),
        ).fetchall()
        return [dict(r) for r in rows]
