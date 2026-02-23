from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from app.core.config import CHROMA_PATH
import re

# Embeddings
embeddings = OpenAIEmbeddings()



# Get Vector Store
def get_vectorstore():
    return Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings
    )

# SECTION + HYBRID CHUNKING (FINAL FIX)
def chunk_by_section(documents):
    """
    Robust section-based chunking for structured documents
    like employee handbooks.

    - Combines section header + content
    - Prevents small sections from being lost
    - Applies secondary semantic splitting for large sections
    """

    # Matches:
    # 1. INTRODUCTION
    # 1.1 ABOUT SOFT SUAVE
    # 2.3 LEAVE POLICY
    section_pattern = r"(\d+\.\d*\.?\s+[A-Z][A-Z\s]+)"

    # Secondary splitter for large sections
    semantic_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )

    new_chunks = []
    for doc in documents:
        text = doc.page_content

        # Split into sections
        splits = re.split(section_pattern, text)

        current_section = "General"

        i = 0
        while i < len(splits):

            part = splits[i].strip()

            if not part:
                i += 1
                continue

            # If it's a section header
            if re.match(section_pattern, part):
                current_section = part

                # Combine with next block (content)
                if i + 1 < len(splits):
                    content = splits[i + 1].strip()

                    combined_text = f"{current_section}\n{content}"

                    # If section is small → keep as single chunk
                    if len(combined_text.split()) < 120:
                        new_chunks.append(
                            Document(
                                page_content=combined_text,
                                metadata={
                                    "section": current_section,
                                    "source": doc.metadata.get("source", "handbook")
                                }
                            )
                        )
                    else:
                        # Large section → semantic split
                        sub_chunks = semantic_splitter.split_text(combined_text)

                        for sub in sub_chunks:
                            new_chunks.append(
                                Document(
                                    page_content=sub,
                                    metadata={
                                        "section": current_section,
                                        "source": doc.metadata.get("source", "handbook")
                                    }
                                )
                            )

                i += 2  # Skip header + content
            else:
                # Fallback for content without header
                new_chunks.append(
                    Document(
                        page_content=part,
                        metadata={
                            "section": current_section,
                            "source": doc.metadata.get("source", "handbook")
                        }
                    )
                )
                i += 1

    return new_chunks

#Add Documents to Vector Store
def add_documents_to_vectorstore(documents):
    """
    Chunk documents properly and store in Chroma.
    """

    vectordb = get_vectorstore()

    #Use improved chunking
    chunks = chunk_by_section(documents)

    if not chunks:
        raise ValueError("No chunks created from documents.")

    vectordb.add_documents(chunks)

    print(f"✅ Successfully stored {len(chunks)} chunks in Chroma.")
