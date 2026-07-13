import json
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, GoogleAPIError

import config
from agent.prompts import SYSTEM_PROMPT
from agent.schemas import AgentResponse
from errors import GeminiError, GeminiQuotaError, log_error

genai.configure(api_key=config.GEMINI_API_KEY)

_model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=SYSTEM_PROMPT,
    generation_config=genai.types.GenerationConfig(
        temperature=0.2,
        max_output_tokens=256,
    ),
)

_chats: dict[int, genai.ChatSession] = {}


def _get_chat(chat_id: int) -> genai.ChatSession:
    if chat_id not in _chats:
        _chats[chat_id] = _model.start_chat(history=[])
    return _chats[chat_id]


def reset_chat(chat_id: int) -> None:
    _chats.pop(chat_id, None)


def process_turn(chat_id: int, user_text: str) -> AgentResponse:
    chat = _get_chat(chat_id)

    try:
        response = chat.send_message(user_text)
    except ResourceExhausted as e:
        log_error("Gemini quota exhausted", e)
        raise GeminiQuotaError("Gemini free-tier quota exceeded") from e
    except GoogleAPIError as e:
        log_error("Gemini API error", e)
        raise GeminiError(f"Gemini API error: {e}") from e
    except Exception as e:
        log_error("Unexpected error calling Gemini", e)
        raise GeminiError(f"Unexpected Gemini error: {e}") from e

    raw = response.text.strip()

    # Strip markdown code fences if Gemini wraps the JSON
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        data = json.loads(raw)
        return AgentResponse(**data)
    except (json.JSONDecodeError, ValueError):
        # Gemini returned non-JSON — ask user to rephrase, don't crash
        return AgentResponse(
            reply_text="Sorry, I didn't quite catch that. Could you rephrase?",
            action="clarify",
        )
