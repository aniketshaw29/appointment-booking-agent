from flask import Flask, request, jsonify, abort, render_template
import json
import hmac
from datetime import datetime

import config
from errors import (
    GeminiQuotaError, GeminiError,
    CalendarAuthError, CalendarError,
    BookingConflictError,
    MESSAGES, log_error, logger,
)
from telephony.telegram_sender import send_message
from calendar_service.db import init_db, get_or_create_session, save_session, create_booking
from calendar_service.google_cal import check_availability, create_event, next_available_slot
from agent.conversation import process_turn, reset_chat

app = Flask(__name__)

with app.app_context():
    init_db()


def _verify_telegram(req) -> bool:
    secret = config.TELEGRAM_WEBHOOK_SECRET
    if not secret:
        return True
    token = req.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    return hmac.compare_digest(token, secret)


@app.route("/webhook", methods=["POST"])
def webhook():
    if not _verify_telegram(request):
        abort(403)

    update = request.get_json(silent=True)
    if not update:
        return jsonify(ok=True)

    message = update.get("message") or update.get("edited_message")
    if not message:
        return jsonify(ok=True)

    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()
    username = message["from"].get("username")

    if not text:
        return jsonify(ok=True)

    session = get_or_create_session(chat_id)

    # ── Built-in commands ────────────────────────────────────────────────────
    if text == "/start":
        reset_chat(chat_id)
        save_session(chat_id, [], "COLLECT_NAME")
        send_message(chat_id, f"Hi! I can help you book an appointment at {config.BUSINESS_NAME}. What's your name?")
        return jsonify(ok=True)

    if text == "/cancel":
        reset_chat(chat_id)
        save_session(chat_id, [], "COLLECT_NAME")
        send_message(chat_id, "No problem! Booking cancelled. Send /start to begin again.")
        return jsonify(ok=True)

    if text == "/help":
        send_message(chat_id, (
            f"*{config.BUSINESS_NAME} Appointment Bot*\n\n"
            f"Commands:\n"
            f"/start — start a new booking\n"
            f"/cancel — cancel current booking\n"
            f"/help — show this message\n\n"
            f"Business hours: {config.BUSINESS_HOURS}\n"
            f"Appointment duration: {config.APPOINTMENT_DURATION_MINUTES} minutes"
        ))
        return jsonify(ok=True)

    # ── AI turn ──────────────────────────────────────────────────────────────
    try:
        response = process_turn(chat_id, text)
    except GeminiQuotaError:
        send_message(chat_id, MESSAGES["gemini_quota"])
        return jsonify(ok=True)
    except GeminiError as e:
        log_error(f"Gemini failed for chat_id={chat_id}", e)
        send_message(chat_id, MESSAGES["gemini_error"])
        return jsonify(ok=True)
    except Exception as e:
        log_error(f"Unexpected error in process_turn for chat_id={chat_id}", e)
        send_message(chat_id, MESSAGES["unknown"])
        return jsonify(ok=True)

    # Carry forward all collected fields
    name     = response.extracted_name     or session.get("name")
    age      = response.extracted_age      or session.get("age")
    location = response.extracted_location or session.get("location")
    nature   = response.extracted_nature   or session.get("nature")
    purpose  = response.extracted_purpose  or session.get("purpose")
    slot     = response.proposed_slot      or session.get("proposed_slot")
    reply    = response.reply_text

    # ── Calendar actions ─────────────────────────────────────────────────────
    if response.action == "check_availability" and slot:
        try:
            free = check_availability(slot)
            if free:
                reply = (
                    f"Great news — {_fmt(slot)} is available! "
                    f"Shall I confirm the booking for {name}? (yes/no)"
                )
            else:
                alt = next_available_slot(slot)
                if alt:
                    slot = alt
                    reply = (
                        f"Sorry, that slot is taken. "
                        f"The next available time is {_fmt(alt)} — would that work for you?"
                    )
                else:
                    reply = MESSAGES["no_slots"]

        except BookingConflictError:
            reply = MESSAGES["slot_in_past"]

        except CalendarAuthError as e:
            log_error(f"Calendar auth error for chat_id={chat_id}", e)
            reply = MESSAGES["calendar_auth"]

        except CalendarError as e:
            log_error(f"Calendar error for chat_id={chat_id}", e)
            reply = MESSAGES["calendar_error"]

    elif response.action == "book" and slot:
        try:
            event_id = create_event(
                name or "Guest", username, slot,
                age=age, location=location, nature=nature, purpose=purpose
            )
            create_booking(
                chat_id, name or "Guest", username, slot, event_id,
                age=age, location=location, nature=nature, purpose=purpose
            )
            logger.info("Booking confirmed: chat_id=%s name=%s slot=%s event_id=%s",
                        chat_id, name, slot, event_id)
            reply = (
                f"Done! Your appointment is confirmed for {_fmt(slot)}. "
                f"A calendar invite has been created. See you then! 🎉\n\n"
                f"Send /start to book another appointment."
            )
            reset_chat(chat_id)
            save_session(chat_id, [], "COLLECT_NAME")
            send_message(chat_id, reply)
            return jsonify(ok=True)

        except BookingConflictError:
            reply = MESSAGES["slot_in_past"]

        except CalendarAuthError as e:
            log_error(f"Calendar auth error during booking for chat_id={chat_id}", e)
            reply = MESSAGES["calendar_auth"]

        except CalendarError as e:
            log_error(f"Calendar error during booking for chat_id={chat_id}", e)
            reply = MESSAGES["booking_failed"]

        except Exception as e:
            log_error(f"Unexpected booking error for chat_id={chat_id}", e)
            reply = MESSAGES["booking_failed"]

    elif response.action == "done":
        reset_chat(chat_id)
        save_session(chat_id, [], "COLLECT_NAME")

    # Persist session
    history = json.loads(session.get("history", "[]"))
    history.append({"role": "user", "content": text})
    history.append({"role": "assistant", "content": reply})

    save_session(chat_id, history, response.action.upper(),
                 name=name, age=age, location=location,
                 nature=nature, purpose=purpose, proposed_slot=slot)
    send_message(chat_id, reply)
    return jsonify(ok=True)


def _fmt(iso: str) -> str:
    dt = datetime.fromisoformat(iso)
    return dt.strftime("%A, %d %B at %I:%M %p").replace(" 0", " ")


@app.route("/", methods=["GET"])
def index():
    return render_template(
        "index.html",
        business_name=config.BUSINESS_NAME,
        business_hours=config.BUSINESS_HOURS,
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok", business=config.BUSINESS_NAME)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
