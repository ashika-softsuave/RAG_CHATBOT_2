def is_doc_question(query: str):
    keywords = ["document", "pdf", "file", "according to"]
    return any(k in query.lower() for k in keywords)
