import socketio
from app.services.chat_service import handle_chat

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
    query = data.get("question")

    if not query:
        return

    session = await sio.get_session(sid)

    awaiting_followup = session.get("awaiting_followup", False)
    last_context = session.get("last_context")
    last_followup_question = session.get("last_followup_question")
    history = session.get("history", [])

    #Call your existing business logic
    result = handle_chat(
        query=query,
        history=history,
        awaiting_followup=awaiting_followup,
        last_context=last_context,
        last_followup_question=last_followup_question
    )

    reply = result["reply"]

    # STREAM WORD BY WORD (Smooth ChatGPT-like effect)
    words = reply.split(" ")

    for word in words:
        await sio.emit("chat_token", word + " ", to=sid)
        await sio.sleep(0.03)  # controls typing speed

    await sio.emit("chat_complete", {"status": "done"}, to=sid)

    # UPDATE SESSION STATE
    session["awaiting_followup"] = result["awaiting_followup"]
    session["last_context"] = result["last_context"]
    session["last_followup_question"] = result["last_followup_question"]

    session["history"].append(f"User: {query}")
    session["history"].append(f"Assistant: {reply}")

    await sio.save_session(sid, session)
