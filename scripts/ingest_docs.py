import os
import sys

# Add project root to path so we can import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.vectorstore.chroma_db import get_vectorstore
from app.core.config import UPLOAD_DIR

def ingest_docs():
    pdf_path = os.path.join(UPLOAD_DIR, "SS Employee Handbook Updated-2025 (1).pdf")
    
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        return

    print(f"Loading document from {pdf_path}...")
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    
    print(f"Loaded {len(docs)} pages.")

    print("Splitting documents...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        add_start_index=True
    )
    splits = text_splitter.split_documents(docs)
    print(f"Created {len(splits)} chunks.")

    print("Adding to vectorstore...")
    vectorstore = get_vectorstore()
    vectorstore.add_documents(splits)
    print("Ingestion complete!")

if __name__ == "__main__":
    ingest_docs()
