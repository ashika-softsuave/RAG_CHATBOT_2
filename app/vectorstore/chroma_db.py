from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from app.core.config import CHROMA_PATH
import re
from langchain.schema import Document

# Embeddings
embeddings = OpenAIEmbeddings()

# Get Vector Store
def get_vectorstore():
    return Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings
    )

# SECTION-BASED CHUNKING
def chunk_by_section(documents):
    """
    Split handbook by section headings like:
    1. INTRODUCTION
    1.1 ABOUT SOFT SUAVE
    1.2 OUR VALUES
    """

    # Improved regex for headings like:
    # 1. INTRODUCTION
    # 1.1 ABOUT SOFT SUAVE
    section_pattern = r"\n(\d+\.\d*\.?\s+[A-Z][A-Z\s]+)"

    new_chunks = []

    for doc in documents:
        text = doc.page_content

        splits = re.split(section_pattern, text)

        current_section = "General"

        for part in splits:
            part = part.strip()
            if not part:
                continue

            if re.match(r"\d+\.\d*\.?\s+[A-Z][A-Z\s]+", part):
                current_section = part
            else:
                new_doc = Document(
                    page_content=part,
                    metadata={
                        "section": current_section,
                        "source": doc.metadata.get("source", "handbook")
                    }
                )
                new_chunks.append(new_doc)

    return new_chunks


# Add Documents to Vector Store
def add_documents_to_vectorstore(documents):
    """
    Chunk documents by section and store in Chroma.
    """

    vectordb = get_vectorstore()

    #Use section-based chunking
    chunks = chunk_by_section(documents)

    vectordb.add_documents(chunks)

    vectordb.persist()