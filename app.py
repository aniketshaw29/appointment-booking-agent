from flask import Flask, request, jsonify, abort, render_template, redirect, url_for, session
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
from agent.llm import process_turn, reset_chat, get_available_models

app = Flask(__name__)
app.secret_key = config.ADMIN_PASSWORD  # used for Flask session (admin login)

# Runtime model state — starts from env var, admin can change without restart
_active_model = config.ACTIVE_MODEL

with app.app_context():
    init_db()
    import os
    cred_path = config.GOOGLE_SERVICE_ACCOUNT_FILE
    logger.info("Service account path: %s — exists: %s", cred_path, os.path.exists(cred_path))


def _verify_telegram(req) -> bool:
    secret = config.TELEGRAM_WEBHOOK_SECRET
    if not secret:
        return True
    token = req.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    return hmac.compare_digest(token, secret)


# ── Telegram webhook ─────────────────────────────────────────────────────────

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

    sess = get_or_create_session(chat_id)

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

    try:
        history = json.loads(sess.get("history", "[]"))
        response = process_turn(chat_id, text, model_id=_active_model, history=history)
    except GeminiQuotaError:
        send_message(chat_id, MESSAGES["gemini_quota"])
        return jsonify(ok=True)
    except GeminiError as e:
        log_error(f"LLM failed for chat_id={chat_id}", e)
        send_message(chat_id, MESSAGES["gemini_error"])
        return jsonify(ok=True)
    except Exception as e:
        log_error(f"Unexpected error for chat_id={chat_id}", e)
        send_message(chat_id, MESSAGES["unknown"])
        return jsonify(ok=True)

    name     = response.extracted_name     or sess.get("name")
    age      = response.extracted_age      or sess.get("age")
    location = response.extracted_location or sess.get("location")
    nature   = response.extracted_nature   or sess.get("nature")
    purpose  = response.extracted_purpose  or sess.get("purpose")
    duration = response.extracted_duration or sess.get("duration")
    slot     = response.proposed_slot      or sess.get("proposed_slot")
    reply    = response.reply_text

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
                age=age, location=location, nature=nature, purpose=purpose,
                duration=duration
            )
            create_booking(
                chat_id, name or "Guest", username, slot, event_id,
                age=age, location=location, nature=nature, purpose=purpose,
                duration=duration
            )
            logger.info("Booking confirmed: chat_id=%s name=%s slot=%s model=%s",
                        chat_id, name, slot, _active_model)
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

    history = json.loads(sess.get("history", "[]"))
    history.append({"role": "user", "content": text})
    history.append({"role": "assistant", "content": reply})

    save_session(chat_id, history, response.action.upper(),
                 name=name, age=age, location=location,
                 nature=nature, purpose=purpose, duration=duration,
                 proposed_slot=slot)
    send_message(chat_id, reply)
    return jsonify(ok=True)


# ── Admin panel ──────────────────────────────────────────────────────────────

@app.route("/admin", methods=["GET"])
def admin():
    if not session.get("admin_logged_in"):
        return render_template("admin_login.html")
    return render_template(
        "admin.html",
        active_model=_active_model,
        models=get_available_models(),
        business_name=config.BUSINESS_NAME,
        openai_configured=bool(config.OPENAI_API_KEY),
    )


@app.route("/admin/login", methods=["POST"])
def admin_login():
    password = request.form.get("password", "")
    if hmac.compare_digest(password, config.ADMIN_PASSWORD):
        session["admin_logged_in"] = True
        return redirect(url_for("admin"))
    return render_template("admin_login.html", error="Incorrect password")


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin"))


@app.route("/admin/set-model", methods=["POST"])
def admin_set_model():
    global _active_model
    if not session.get("admin_logged_in"):
        abort(403)
    model_id = request.form.get("model_id", "")
    from agent.llm import ALL_MODELS
    if model_id not in ALL_MODELS:
        return render_template("admin.html",
            active_model=_active_model,
            models=get_available_models(),
            business_name=config.BUSINESS_NAME,
            openai_configured=bool(config.OPENAI_API_KEY),
            error=f"Unknown model: {model_id}")
    _active_model = model_id
    logger.info("Admin switched model to: %s", _active_model)
    return redirect(url_for("admin"))


# ── Public routes ─────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def index():
    return render_template(
        "index.html",
        business_name=config.BUSINESS_NAME,
        business_hours=config.BUSINESS_HOURS,
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok", business=config.BUSINESS_NAME, model=_active_model)


def _fmt(iso: str) -> str:
    dt = datetime.fromisoformat(iso)
    return dt.strftime("%A, %d %B at %I:%M %p").replace(" 0", " ")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
