import socketio
from app.services.chat_service import handle_chat
from app.db.database import SessionLocal
from app.db.models import ChatMessage
from app.services.memory_service import handle_summarization, load_memory
# Create async Socket.IO server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*"
)

# CONNECTION EVENTS
@sio.event
async def connect(sid, environ):
    print(f"Socket connected: {sid}")

    # Initialize per-client session state
    await sio.save_session(sid, {
        "awaiting_followup": False,
        "last_context": None,
        "last_followup_question": None,
        "history": []
    })

@sio.event
async def disconnect(sid):
    print(f"Socket disconnected: {sid}")

# MAIN CHAT EVENT
@sio.event
async def chat_message(sid, data):
    print("CHAT EVENT RECEIVED:", data)
    query = data.get("question")
    print("Extracted query:", query)
    chat_id = data.get("chat_id")

    if not query:
        return

    #If frontend didn't send chat_id, use socket id
    if not chat_id:
        chat_id = sid
    db = SessionLocal()

    #SAVE USER MESSAGE
    user_msg = ChatMessage(
        chat_id=chat_id,
        role="user",
        content=query
    )
    db.add(user_msg)
    db.commit()

    #SUMMARIZE IF NEEDED (after 10 msgs)
    handle_summarization(db, chat_id)

    # LOAD MEMORY (summary + recent)
    summary_text, recent_text = load_memory(db, chat_id)

    memory_block = f"""
Previous Summary:
{summary_text}

Recent Conversation:
{recent_text}
"""

    #GET SESSION STATE (KEEP YOUR LOGIC)
    session = await sio.get_session(sid)

    awaiting_followup = session.get("awaiting_followup", False)
    last_context = session.get("last_context")
    last_followup_question = session.get("last_followup_question")
    print("Calling handle_chat...")
    #CALL EXISTING BUSINESS LOGIC
    try:
        result = handle_chat(
            query=query,
            history=[memory_block],
            awaiting_followup=awaiting_followup,
            last_context=last_context,
            last_followup_question=last_followup_question
        )
    except Exception as e:
        print("HANDLE_CHAT ERROR:", e)
        await sio.emit("chat_token", "Internal error occurred.", to=sid)
        await sio.emit("chat_complete", {"status": "done"}, to=sid)
        return
    print("Result from handle_chat:", result)
    reply = result.get("reply", "")
    print("Reply before streaming:", reply)

    if not reply:
        reply = "The requested information is not available."

    # SAVE ASSISTANT MESSAGE
    assistant_msg = ChatMessage(
        chat_id=chat_id,
        role="assistant",
        content=reply
    )
    db.add(assistant_msg)
    db.commit()

    db.close()


    # STREAM WORD BY WORD (KEEP EXISTING)
    words = reply.split(" ")

    for word in words:
        await sio.emit("chat_token", word + " ", to=sid)
        await sio.sleep(0.03)

    await sio.emit("chat_complete", {"status": "done"}, to=sid)

    #UPDATE SESSION STATE (KEEP EXISTING)
    session["awaiting_followup"] = result["awaiting_followup"]
    session["last_context"] = result["last_context"]
    session["last_followup_question"] = result["last_followup_question"]

    await sio.save_session(sid, session)
