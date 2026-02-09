from fastapi import APIRouter
import shutil, os
from app.schemas.chat import ChatRequest
from app.services.chat_service import handle_chat
from fastapi import Depends
from app.auth.jwt_auth import get_current_user
router = APIRouter(prefix="/chat", tags=["Chat"])
@router.post("/")
def chat(req: ChatRequest, user: str = Depends(get_current_user)):
    reply = handle_chat(
        req.query,
        req.history,
        req.followup_answer
    )
    return {"reply": reply}