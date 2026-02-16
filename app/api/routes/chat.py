from fastapi import APIRouter
import shutil, os
from app.schemas.chat import ChatRequest
from app.services.chat_service import handle_chat
from fastapi import Depends
from app.auth.jwt_auth import get_current_user
router = APIRouter(prefix="/chat", tags=["Chat"])
@router.post("/")
def chat(req: ChatRequest, user: str = Depends(get_current_user)):
    result = handle_chat(
        query=req.query,
        history=req.history,
        followup_answer=req.followup_answer,
        awaiting_followup=req.awaiting_followup,
        last_context=req.last_context,
        last_followup_question=req.last_followup_question
    )
    return result
