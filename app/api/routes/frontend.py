from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.templates import templates
router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})
