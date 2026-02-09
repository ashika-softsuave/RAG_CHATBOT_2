from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from app.api.routes import chat, admin_upload
from app.api.routes import auth
from app.db.database import engine
from app.db import models
app = FastAPI(title="RAG Chatbot")

models.Base.metadata.create_all(bind=engine)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(admin_upload.router)
