from pydantic import BaseModel
from typing import Literal


class AgentResponse(BaseModel):
    reply_text: str
    action: Literal["clarify", "check_availability", "book", "done"]
    extracted_name: str | None = None
    extracted_age: str | None = None
    extracted_location: str | None = None
    extracted_nature: str | None = None      # work | business | casual | other
    extracted_purpose: str | None = None     # free-text purpose of meeting
    extracted_duration: str | None = None    # duration in minutes e.g. "15"
    proposed_slot: str | None = None
