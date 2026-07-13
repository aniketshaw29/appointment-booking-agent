"""
Unified LLM interface — routes to Gemini or OpenAI based on active model setting.
Add a new provider by adding a block in _call_model().
"""
import json
import logging

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, GoogleAPIError
from openai import OpenAI, RateLimitError as OpenAIRateLimitError, APIError as OpenAIAPIError

import config
from agent.prompts import SYSTEM_PROMPT
from agent.schemas import AgentResponse
from errors import GeminiError, GeminiQuotaError, log_error

logger = logging.getLogger("booking_bot")

# ── Gemini setup ──────────────────────────────────────────────────────────────
genai.configure(api_key=config.GEMINI_API_KEY)

GEMINI_MODELS = {
    "gemini-2.5-flash": "gemini-2.5-flash",
    "gemini-2.0-flash": "gemini-2.0-flash",
}

OPENAI_MODELS = {
    "gpt-4o-mini": "gpt-4o-mini",
    "gpt-4o":      "gpt-4o",
}

ALL_MODELS = {
    **{k: {"provider": "gemini", "label": k} for k in GEMINI_MODELS},
    **{k: {"provider": "openai", "label": k} for k in OPENAI_MODELS},
}

DEFAULT_MODEL = "gemini-2.5-flash"

# In-memory Gemini chat sessions per chat_id
_gemini_chats: dict[int, genai.ChatSession] = {}
# In-memory OpenAI message history per chat_id
_openai_histories: dict[int, list[dict]] = {}


def get_available_models() -> list[dict]:
    """Return list of {id, label, provider} for the admin UI."""
    return [
        {"id": k, "label": v["label"], "provider": v["provider"]}
        for k, v in ALL_MODELS.items()
    ]


def reset_chat(chat_id: int) -> None:
    _gemini_chats.pop(chat_id, None)
    _openai_histories.pop(chat_id, None)


def process_turn(chat_id: int, user_text: str, model_id: str | None = None) -> AgentResponse:
    """
    Process one conversation turn using the specified (or default) model.
    Raises GeminiQuotaError, GeminiError on failure.
    """
    active = model_id or DEFAULT_MODEL
    provider = ALL_MODELS.get(active, {}).get("provider", "gemini")

    logger.info("chat_id=%s model=%s provider=%s", chat_id, active, provider)

    if provider == "gemini":
        return _call_gemini(chat_id, user_text, active)
    elif provider == "openai":
        return _call_openai(chat_id, user_text, active)
    else:
        raise GeminiError(f"Unknown provider: {provider}")


# ── Gemini ────────────────────────────────────────────────────────────────────

def _get_gemini_chat(chat_id: int, model_id: str) -> genai.ChatSession:
    if chat_id not in _gemini_chats:
        model = genai.GenerativeModel(
            model_name=model_id,
            system_instruction=SYSTEM_PROMPT,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=512,
            ),
        )
        _gemini_chats[chat_id] = model.start_chat(history=[])
    return _gemini_chats[chat_id]


def _call_gemini(chat_id: int, user_text: str, model_id: str) -> AgentResponse:
    chat = _get_gemini_chat(chat_id, model_id)
    try:
        response = chat.send_message(user_text)
    except ResourceExhausted as e:
        log_error("Gemini quota exhausted", e)
        raise GeminiQuotaError("Gemini quota exceeded") from e
    except GoogleAPIError as e:
        log_error("Gemini API error", e)
        raise GeminiError(str(e)) from e
    except Exception as e:
        log_error("Unexpected Gemini error", e)
        raise GeminiError(str(e)) from e

    return _parse_response(response.text)


# ── OpenAI ────────────────────────────────────────────────────────────────────

def _get_openai_history(chat_id: int) -> list[dict]:
    if chat_id not in _openai_histories:
        _openai_histories[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return _openai_histories[chat_id]


def _call_openai(chat_id: int, user_text: str, model_id: str) -> AgentResponse:
    if not config.OPENAI_API_KEY:
        raise GeminiError("OpenAI API key not configured")

    history = _get_openai_history(chat_id)
    history.append({"role": "user", "content": user_text})

    try:
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        completion = client.chat.completions.create(
            model=model_id,
            messages=history,
            temperature=0.2,
            max_tokens=512,
        )
        raw = completion.choices[0].message.content or ""
        history.append({"role": "assistant", "content": raw})
    except OpenAIRateLimitError as e:
        log_error("OpenAI rate limit", e)
        raise GeminiQuotaError("OpenAI quota exceeded") from e
    except OpenAIAPIError as e:
        log_error("OpenAI API error", e)
        raise GeminiError(str(e)) from e
    except Exception as e:
        log_error("Unexpected OpenAI error", e)
        raise GeminiError(str(e)) from e

    return _parse_response(raw)


# ── Shared response parser ────────────────────────────────────────────────────

def _parse_response(raw: str) -> AgentResponse:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    try:
        return AgentResponse(**json.loads(raw))
    except (json.JSONDecodeError, ValueError):
        return AgentResponse(
            reply_text="Sorry, I didn't quite catch that. Could you rephrase?",
            action="clarify",
        )
