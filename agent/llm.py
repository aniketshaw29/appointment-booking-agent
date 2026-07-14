"""
Unified LLM interface — routes to Gemini or OpenAI based on active model setting.
"""
import json
import logging

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, GoogleAPIError
from openai import OpenAI, RateLimitError as OpenAIRateLimitError, APIError as OpenAIAPIError

import config
from agent.prompts import get_system_prompt
from agent.schemas import AgentResponse
from errors import GeminiError, GeminiQuotaError, log_error

logger = logging.getLogger("booking_bot")

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


def get_available_models() -> list[dict]:
    return [
        {"id": k, "label": v["label"], "provider": v["provider"]}
        for k, v in ALL_MODELS.items()
    ]


def reset_chat(chat_id: int) -> None:
    # Nothing to clear — we rebuild from SQLite history on every turn now
    pass


def process_turn(chat_id: int, user_text: str, model_id: str | None = None,
                 history: list | None = None) -> AgentResponse:
    """
    Process one conversation turn.
    history: list of {role, content} dicts from SQLite (source of truth).
    The LLM session is rebuilt from this history each call to stay in sync.
    """
    active = model_id or DEFAULT_MODEL
    provider = ALL_MODELS.get(active, {}).get("provider", "gemini")
    prior = history or []

    logger.info("chat_id=%s model=%s turns=%d", chat_id, active, len(prior))

    if provider == "gemini":
        return _call_gemini(user_text, active, prior)
    elif provider == "openai":
        return _call_openai(user_text, active, prior)
    else:
        raise GeminiError(f"Unknown provider: {provider}")


# ── Gemini ────────────────────────────────────────────────────────────────────

def _call_gemini(user_text: str, model_id: str, prior: list) -> AgentResponse:
    """Rebuild the Gemini chat from SQLite history on every call."""
    system_prompt = get_system_prompt()  # fresh prompt with today's date

    gemini_history = []
    for turn in prior:
        role = "user" if turn["role"] == "user" else "model"
        gemini_history.append({"role": role, "parts": [{"text": turn["content"]}]})

    model = genai.GenerativeModel(
        model_name=model_id,
        system_instruction=system_prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.2,
            max_output_tokens=512,
        ),
    )
    chat = model.start_chat(history=gemini_history)

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

def _call_openai(user_text: str, model_id: str, prior: list) -> AgentResponse:
    if not config.OPENAI_API_KEY:
        raise GeminiError("OpenAI API key not configured")

    system_prompt = get_system_prompt()
    messages = [{"role": "system", "content": system_prompt}]
    for turn in prior:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user_text})

    try:
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        completion = client.chat.completions.create(
            model=model_id,
            messages=messages,
            temperature=0.2,
            max_tokens=512,
        )
        raw = completion.choices[0].message.content or ""
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
        obj = AgentResponse(**json.loads(raw))
        obj.raw_json = raw   # keep the original JSON for history rebuilding
        return obj
    except (json.JSONDecodeError, ValueError):
        fallback = AgentResponse(
            reply_text="Sorry, I didn't quite catch that. Could you rephrase?",
            action="clarify",
        )
        fallback.raw_json = json.dumps({"reply_text": fallback.reply_text, "action": "clarify"})
        return fallback
