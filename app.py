from flask import Flask, request, jsonify
import config
from telephony.telegram_sender import send_message

app = Flask(__name__)


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

    if not text:
        return jsonify(ok=True)

    # Echo back for now — ConversationManager wired in Phase 3
    reply = f"You said: {text}"
    send_message(chat_id, reply)

    return jsonify(ok=True)


@app.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok", business=config.BUSINESS_NAME)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
