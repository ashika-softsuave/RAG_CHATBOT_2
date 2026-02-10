from app.vectorstore.chroma_db import get_vectorstore
from app.core.llm import llm

def rag_answer(query: str, history: list[str]) -> str | None:
    """
    Returns an answer ONLY if found in SoftSuave documents.
    Returns None if answer is not present.
    """

    vectordb = get_vectorstore()
    docs = vectordb.similarity_search(query, k=3)

    if not docs:
        return None

    context = "\n\n".join(d.page_content for d in docs)

    prompt = f"""
You are SoftSuave's internal AI assistant.

Rules:
- Answer ONLY using the provided context.
- Do NOT use external knowledge.
- Do NOT guess or assume.
- If the answer is not explicitly present in the context, return NOTHING.


Context:
{context}

Question:
{query}
"""

    answer = llm.invoke(prompt).content.strip()

    # Final guardrail
    if not answer or len(answer) < 30:
        return None

    return answer
