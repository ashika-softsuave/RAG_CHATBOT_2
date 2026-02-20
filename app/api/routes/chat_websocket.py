from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.chat_service import handle_chat

chat_ws_router = APIRouter(prefix="/chat", tags=["Chat"])

@chat_ws_router.websocket("/ws")
async def chat_ws(websocket: WebSocket):
    await websocket.accept()
    #To maintain conversation state per client
    awaiting_followup = False
    last_context = None
    last_followup_question = None
    history = []

    try:
        while True:
            query = await websocket.receive_text()

            result = handle_chat(
                query=query,
                history=history,
                awaiting_followup=awaiting_followup,
                last_context=last_context,
                last_followup_question=last_followup_question
            )

            reply = result["reply"]

            # Stream token by token
            for char in reply:
                await websocket.send_text(char)

            await websocket.send_text("[END]")

            # Update state
            awaiting_followup = result["awaiting_followup"]
            last_context = result["last_context"]
            last_followup_question = result["last_followup_question"]

            history.append(f"User: {query}")
            history.append(f"Assistant: {reply}")

    except WebSocketDisconnect:
        print("Client disconnected")
