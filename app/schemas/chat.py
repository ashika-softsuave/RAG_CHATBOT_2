from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    query: str
    history: Optional[List[str]] = []
    followup_answer: Optional[str] = None
