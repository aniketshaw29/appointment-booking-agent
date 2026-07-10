# Conversation Flow

## Dialog State Machine

```
START
  └─► COLLECT_NAME
        └─► COLLECT_DATETIME
              └─► CHECK_AVAILABILITY ──► OFFER_ALTERNATIVE ─┐
                    │                         ▲              │
                    └─► CONFIRM_BOOKING ──────┘              │
                          ├─► yes → BOOK_AND_END             │
                          └─► no  → COLLECT_DATETIME ◄───────┘
```

## State Descriptions

| State | What Gemini Does | Next State |
|---|---|---|
| `COLLECT_NAME` | Extract name from message; ask to repeat if unclear | `COLLECT_DATETIME` |
| `COLLECT_DATETIME` | Parse natural date/time (e.g. "next Tuesday at 3", "tomorrow morning") → ISO8601 | `CHECK_AVAILABILITY` |
| `CHECK_AVAILABILITY` | Python check only (not Gemini). Query freebusy API + SQLite | `CONFIRM_BOOKING` or `OFFER_ALTERNATIVE` |
| `CONFIRM_BOOKING` | Present name + datetime back, ask for yes/no | `BOOK_AND_END` or `COLLECT_DATETIME` |
| `OFFER_ALTERNATIVE` | Present next available slot computed by Python, ask if they want it | `CONFIRM_BOOKING` |
| `BOOK_AND_END` | Python writes SQLite + GCal event. Gemini says goodbye | — |

## Sample Dialog (Telegram)

```
Bot  : "Hi! I can help you book an appointment.
        What's your name?"

User : "It's Sarah"

Bot  : "Thanks Sarah! When would you like to come in?"

User : "Next Wednesday at 2pm"

Bot  : "Let me check... Wednesday July 16th at 2pm works great.
        Shall I book that for you, Sarah? (yes/no)"

User : "Yes please"

Bot  : "Done! You're booked for Wednesday July 16th at 2pm.
        You'll get a calendar invite. See you then, Sarah!"
```

## Gemini JSON Output Format

Every turn Gemini returns structured JSON:

```json
{
  "reply_text": "Thanks Sarah! When would you like to come in?",
  "action": "clarify | check_availability | book | done",
  "extracted_name": "Sarah",
  "proposed_slot": "2026-07-16T14:00:00"
}
```

## Actions Gemini Can Return

| Action | Meaning | Python does next |
|---|---|---|
| `clarify` | Need more info from user | Send `reply_text` back via Telegram |
| `check_availability` | Name + slot both collected | Check Google Calendar, then re-enter loop |
| `book` | User confirmed yes | Write SQLite + GCal, send confirmation message |
| `done` | Booking complete or user says bye | Send goodbye message |

## Error Paths

- **Unrecognized date:** Gemini action = `clarify`, asks user to restate in a different format
- **Slot taken:** Python returns unavailable → Gemini offers next 3 open slots
- **API failure:** Send "Sorry, I'm having trouble right now. Please try again in a moment."
- **User says "cancel":** Gemini detects intent → action = `done`, end conversation cleanly
