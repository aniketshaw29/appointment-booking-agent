from flask import Flask, request, jsonify
import config
from telephony.telegram_sender import send_message
from calendar_service.db import init_db, get_or_create_session, save_session, create_booking
from agent.conversation import process_turn, reset_chat

app = Flask(__name__)

with app.app_context():
    init_db()


@app.route("/webhook", methods=["POST"])
def webhook():
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

    # Load or create session state
    session = get_or_create_session(chat_id)

    # Handle /start — reset conversation
    if text == "/start":
        reset_chat(chat_id)
        save_session(chat_id, [], "COLLECT_NAME", None, None)
        send_message(chat_id, f"Hi! I can help you book an appointment at {config.BUSINESS_NAME}. What's your name?")
        return jsonify(ok=True)

    # Process turn through Gemini
    try:
        response = process_turn(chat_id, text)
    except Exception:
        send_message(chat_id, "Sorry, something went wrong. Please try again.")
        return jsonify(ok=True)

    # Persist updated session
    import json
    history = json.loads(session.get("history", "[]"))
    history.append({"role": "user", "content": text})
    history.append({"role": "assistant", "content": response.reply_text})

    save_session(
        chat_id,
        history,
        response.action.upper(),
        response.extracted_name or session.get("name"),
        response.proposed_slot or session.get("proposed_slot"),
    )

    # If booking confirmed, save to DB
    if response.action == "book" and response.proposed_slot:
        name = response.extracted_name or session.get("name") or "Guest"
        create_booking(chat_id, name, username, response.proposed_slot)

    send_message(chat_id, response.reply_text)
    return jsonify(ok=True)


@app.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok", business=config.BUSINESS_NAME)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
