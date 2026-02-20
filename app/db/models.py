from sqlalchemy import Column, Integer, String
from app.db.database import Base
from sqlalchemy import  Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, index=True)
    role = Column(String)  # "user" or "assistant"
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatSummary(Base):
    __tablename__ = "chat_summaries"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String, index=True)
    summary_text = Column(Text)
    last_message_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
