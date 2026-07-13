# Conversation Flow

## Dialog State Machine

```
START
  └─► COLLECT_NAME
        └─► COLLECT_AGE
              └─► COLLECT_LOCATION
                    └─► COLLECT_NATURE (work/business/casual/other)
                          └─► COLLECT_PURPOSE
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
| `COLLECT_NAME` | Extract name | `COLLECT_AGE` |
| `COLLECT_AGE` | Extract age | `COLLECT_LOCATION` |
| `COLLECT_LOCATION` | Extract city/area | `COLLECT_NATURE` |
| `COLLECT_NATURE` | Classify as work / business / casual / other | `COLLECT_PURPOSE` |
| `COLLECT_PURPOSE` | Extract brief purpose of the meeting | `COLLECT_DATETIME` |
| `COLLECT_DATETIME` | Parse natural date/time → ISO8601 | `CHECK_AVAILABILITY` |
| `CHECK_AVAILABILITY` | Python check only. Query freebusy API + SQLite | `CONFIRM_BOOKING` or `OFFER_ALTERNATIVE` |
| `CONFIRM_BOOKING` | Present name + datetime back, ask yes/no | `BOOK_AND_END` or `COLLECT_DATETIME` |
| `OFFER_ALTERNATIVE` | Present next available slot | `CONFIRM_BOOKING` |
| `BOOK_AND_END` | Python writes SQLite + GCal event. Gemini says goodbye | — |

## Sample Dialog

```
Bot  : "Hi! I can help you book an appointment at [Business]. What's your name?"
User : "I'm Priya"

Bot  : "Nice to meet you, Priya! How old are you?"
User : "27"

Bot  : "Where are you located?"
User : "Pune"

Bot  : "Is this for work, business, or something casual?"
User : "Business"

Bot  : "Got it! Briefly, what would you like to discuss?"
User : "Partnership proposal for my startup"

Bot  : "Great! When would you like to come in?"
User : "Next Monday at 11am"

Bot  : "Let me check... Monday, 20 July at 11:00 AM is available!
        Shall I confirm the booking for Priya? (yes/no)"
User : "Yes"

Bot  : "Done! Your appointment is confirmed for Monday, 20 July at 11:00 AM.
        A calendar invite has been created. See you then! 🎉"
```

## Gemini JSON Output Format

Every turn Gemini returns:

```json
{
  "reply_text": "Nice to meet you, Priya! How old are you?",
  "action": "clarify | check_availability | book | done",
  "extracted_name": "Priya",
  "extracted_age": "27",
  "extracted_location": "Pune",
  "extracted_nature": "business",
  "extracted_purpose": "Partnership proposal for my startup",
  "proposed_slot": "2026-07-20T11:00:00"
}
```

## Actions Gemini Can Return

| Action | Meaning | Python does next |
|---|---|---|
| `clarify` | Still collecting details or date unclear | Send reply_text back via Telegram |
| `check_availability` | All fields + slot collected | Check Google Calendar, re-enter loop |
| `book` | User confirmed yes | Write SQLite + GCal with all details, send confirmation |
| `done` | Booking complete or user says bye | Send goodbye, reset session |

## Data Collected Per Booking

| Field | Example |
|---|---|
| Name | Priya |
| Age | 27 |
| Location | Pune |
| Nature | business |
| Purpose | Partnership proposal for my startup |
| Date/Time | Monday, 20 July at 11:00 AM |

## Error Paths

- **Unrecognized date:** Gemini action = `clarify`, asks to restate
- **Slot taken:** Python finds next free slot and offers it
- **API failure:** Sends "I'm having trouble right now, please try again"
- **User says "cancel":** Gemini detects intent → action = `done`, resets session
