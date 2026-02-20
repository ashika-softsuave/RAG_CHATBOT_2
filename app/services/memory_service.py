from app.core.llm import llm
from app.db.models import ChatMessage, ChatSummary
from sqlalchemy.orm import Session


def summarize_messages(messages: list[str]) -> str:
    prompt = f"""
Summarize the following conversation briefly but preserve key facts,
company details, and important user intents:

{messages}
"""

    return llm.invoke(prompt).content.strip()


def handle_summarization(db: Session, chat_id: str):
    last_summary = (
        db.query(ChatSummary)
        .filter(ChatSummary.chat_id == chat_id)
        .order_by(ChatSummary.id.desc())
        .first()
    )

    last_message_id = last_summary.last_message_id if last_summary else 0

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.chat_id == chat_id)
        .filter(ChatMessage.id > last_message_id)
        .order_by(ChatMessage.id.asc())
        .all()
    )

    if len(messages) < 10:
        return

    raw_text = [
        f"{m.role.upper()}: {m.content}"
        for m in messages
    ]

    summary_text = summarize_messages(raw_text)

    new_summary = ChatSummary(
        chat_id=chat_id,
        summary_text=summary_text,
        last_message_id=messages[-1].id
    )

    db.add(new_summary)
    db.commit()

def load_memory(db: Session, chat_id: str):
    last_summary = (
        db.query(ChatSummary)
        .filter(ChatSummary.chat_id == chat_id)
        .order_by(ChatSummary.id.desc())
        .first()
    )

    summary_text = last_summary.summary_text if last_summary else ""

    recent_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.chat_id == chat_id)
        .order_by(ChatMessage.id.desc())
        .limit(5)
        .all()
    )

    recent_messages.reverse()

    formatted_recent = "\n".join(
        f"{m.role.upper()}: {m.content}"
        for m in recent_messages
    )

    return summary_text, formatted_recent