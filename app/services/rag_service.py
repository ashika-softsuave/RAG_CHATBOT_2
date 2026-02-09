from app.vectorstore.chroma_db import get_vectorstore
from app.core.llm import llm

def rag_answer(query, history):
    vectordb = get_vectorstore()
    docs = vectordb.similarity_search(query, k=3)

    context = "\n".join([d.page_content for d in docs])

    prompt = f"""
Context:
{context}

Chat History:
{history}

Question:
{query}
"""
    return llm.invoke(prompt).content
