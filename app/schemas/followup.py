from pydantic import BaseModel

class FollowUpState(BaseModel):
    last_question: str | None = None
    awaiting_answer: bool = False
