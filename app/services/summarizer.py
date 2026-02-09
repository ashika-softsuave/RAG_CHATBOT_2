from app.core.llm import llm

def summarize_chat(history):
    if len(history) < 10:
        return history

    summary = llm.invoke(
        f"Summarize this chat briefly:\n{history}"
    ).content

    return [summary]
