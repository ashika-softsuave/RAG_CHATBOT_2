from pydantic import BaseModel, Field
from typing import List, Optional

class ChatRequest(BaseModel):
    query: str
    history: List[str] = Field(default_factory=list)
    awaiting_followup: bool = False
    last_context: Optional[str] = None
    last_followup_question: Optional[str] = None