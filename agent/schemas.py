from pydantic import BaseModel
from typing import Literal


class AgentResponse(BaseModel):
    reply_text: str
    action: Literal["clarify", "check_availability", "book", "done"]
    extracted_name: str | None = None
    extracted_age: str | None = None
    extracted_location: str | None = None
    extracted_nature: str | None = None
    extracted_purpose: str | None = None
    extracted_duration: str | None = None
    proposed_slot: str | None = None
    raw_json: str = ""  # original LLM JSON — used to rebuild accurate history
