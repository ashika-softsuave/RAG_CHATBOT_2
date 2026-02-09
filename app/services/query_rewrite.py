from app.core.llm import llm

def rewrite_query(query: str, history: list[str]) -> str:
    """
    Normalizes the user query by:
    - Correcting spelling and grammar
    - Resolving implicit references
    - Anchoring ambiguous references to the main entity in the conversation
    """

    prompt = f"""
You are a language understanding module.

Your tasks:
1. Correct spelling and grammar mistakes.
2. Identify the primary entity or organization being discussed in the conversation.
3. Resolve ALL ambiguous references (e.g., "their", "it", "that company", "your company")
   by explicitly replacing them with the identified entity name.
4. Rewrite the question into a clear, fully self-contained form.
5. Do NOT answer the question.
6. If no rewrite is needed, return the original question.

Conversation context:
{chr(10).join(history) if history else "No prior context."}

User question:
"{query}"

Return ONLY the rewritten question.
"""

    return llm.invoke(prompt).content.strip()
