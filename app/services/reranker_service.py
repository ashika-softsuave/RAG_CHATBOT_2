from sentence_transformers import CrossEncoder

# Load once globally
reranker_model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank_documents(query: str, docs: list, top_k: int = 3):
    """
    Rerank documents using CrossEncoder.
    """

    if not docs:
        return []

    pairs = [(query, doc.page_content) for doc in docs]
    scores = reranker_model.predict(pairs)

    scored_docs = list(zip(docs, scores))
    scored_docs.sort(key=lambda x: x[1], reverse=True)

    reranked = [doc for doc, _ in scored_docs[:top_k]]

    return reranked
