from app.core.llm import llm

def rewrite_query(query: str, history: list[str]) -> str:
    """
    Normalizes the user query for a SoftSuave-only RAG assistant by:
    - Correcting spelling and grammar
    - Resolving implicit references
    - Anchoring ALL references explicitly to SoftSuave
    """

    prompt = f"""
You are a query normalization module for SoftSuave's internal AI assistant.

Context rules:
- The assistant represents ONLY SoftSuave company.
- All ambiguous references must be resolved to "SoftSuave".
- Do NOT introduce any new entities.
- Do NOT answer the question.

Your tasks:
1. Correct spelling and grammar mistakes.
2. Resolve implicit references (e.g., "their", "it", "that company", "your company")
   by explicitly replacing them with "SoftSuave".
3. Rewrite the question into a clear, fully self-contained form.
4. If no rewrite is needed, return the original question unchanged.

Conversation context:
{chr(10).join(history) if history else "No prior context."}

User question:
"{query}"

Return ONLY the rewritten question.
"""

    rewritten = llm.invoke(prompt).content.strip()
    return rewritten
