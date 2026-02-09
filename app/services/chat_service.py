from app.core.llm import llm
from app.services.rag_service import rag_answer
from app.services.summarizer import summarize_chat
from app.services.query_rewrite import rewrite_query
from app.utils.query_router import is_doc_question


def handle_chat(query: str, history: list[str], followup_answer: str | None = None) -> str:
    """
    Core chat handler.
    - Understands natural language
    - Resolves references
    - Uses RAG when relevant
    - Always answers (ChatGPT-like behavior)
    """

    #SAFETY
    history = history or []

    # NATURAL LANGUAGE REWRITE (FULL CONTEXT)
    # This fixes spelling, resolves "their / your company / it", anchors entities
    rewritten_query = rewrite_query(query, history)

    if followup_answer:
        rewritten_query = rewrite_query(
            rewritten_query,
            history + [f"User answered: {followup_answer}"]
        )

    #SUMMARIZE HISTORY (TOKEN CONTROL)
    summarized_history = summarize_chat(history)

    #ANSWERING STRATEGY
    answer = None
    used_rag = False

    # Try RAG first ONLY if it looks document-related
    if is_doc_question(rewritten_query):
        try:
            answer = rag_answer(rewritten_query, summarized_history)
            used_rag = True
        except Exception:
            answer = None  # Fail silently → fallback to LLM

    #ALWAYS FALLBACK TO LLM
    if not answer or len(answer.strip()) < 20:
        llm_prompt = f"""
You are a helpful, confident AI assistant.

Answer the question as best as you can.
- Use reasoning if information is incomplete.
- Do NOT refuse unless unsafe.
- Do NOT mention limitations unless explicitly asked.
- Be clear, concise, and helpful.

Question:
{rewritten_query}
"""
        answer = llm.invoke(llm_prompt).content
        used_rag = False

    #OPTIONAL FOLLOW-UP QUESTION
    if (
        used_rag
        and followup_answer is None
        and len(answer.split()) > 60
    ):
        return f"{answer}\n\n❓ Would you like me to go deeper into this?"

    return answer
# from app.core.llm import llm
# from app.services.rag_service import rag_answer
# from app.services.summarizer import summarize_chat
# from app.services.query_rewrite import rewrite_query
# from app.utils.query_router import is_doc_question
#
# def handle_chat(query, history, followup_answer=None):
#     history = summarize_chat(history)
#
#     # 🔑 Natural language rewrite (always safe)
#     query = rewrite_query(query, history)
#
#     if followup_answer:
#         query = rewrite_query(query, history + [f"User answered: {followup_answer}"])
#
#     if is_doc_question(query):
#         answer = rag_answer(query, history)
#         needs_followup = True
#     else:
#         answer = llm.invoke(query).content
#         needs_followup = False
#
#     if needs_followup and followup_answer is None and len(answer.split()) > 50:
#         return f"{answer}\n\n❓ Do you want more details?"
#
#     return answer
