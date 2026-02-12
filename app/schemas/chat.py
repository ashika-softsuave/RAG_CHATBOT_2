from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    query: str
    history: List[str] = []
    followup_answer: Optional[str] = None
    awaiting_followup: bool = False
    last_context: Optional[str] = None
    last_followup_question: Optional[str] = None
