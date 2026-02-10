from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    query: str
    history: List[str] = []
    followup_answer: Optional[str] = None
