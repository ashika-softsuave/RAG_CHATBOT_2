from dotenv import load_dotenv
load_dotenv()

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from socketio import ASGIApp

from app.api.routes import chat, admin_upload, auth, frontend
from app.db.database import engine
from app.db import models
from app.socket_server import sio

app = FastAPI(title="RAG Chatbot")

models.Base.metadata.create_all(bind=engine)

# ✅ Absolute static path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

print("STATIC DIR:", STATIC_DIR)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(admin_upload.router)
app.include_router(frontend.router)

# ✅ Mount Socket.IO as middleware, NOT replace app
app.mount("/", ASGIApp(sio, other_asgi_app=app))
