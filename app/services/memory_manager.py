from app.services.summarizer import summarize_chat

def manage_memory(chat_history):
    if len(chat_history) >= 10:
        return summarize_chat(chat_history)
    return chat_history
