from pydantic import BaseModel
from typing import Literal


class AgentResponse(BaseModel):
    reply_text: str
    action: Literal["clarify", "check_availability", "book", "done"]
    extracted_name: str | None = None
    proposed_slot: str | None = None
