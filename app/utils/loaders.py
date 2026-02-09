from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader

def load_document(path):
    if path.endswith(".pdf"):
        return PyPDFLoader(path).load()
    if path.endswith(".docx"):
        return Docx2txtLoader(path).load()
