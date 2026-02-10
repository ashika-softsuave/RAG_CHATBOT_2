from app.core.llm import llm

def summarize_chat(history: list[str]) -> list[str]:
    if len(history) < 20:  # 10 user turns ≈ 20 messages
        return history

    prompt = f"""
Summarize the following conversation for future context.
Keep all important details related to SoftSuave documents.

Conversation:
{history}
"""
    summary = llm.invoke(prompt).content.strip()
    return [f"SUMMARY: {summary}"]
