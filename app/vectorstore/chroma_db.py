from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.core.config import CHROMA_PATH

# Embeddings
embeddings = OpenAIEmbeddings()

# Get Vector Store
def get_vectorstore():
    return Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings
    )

# Chunking Function (NEW)
def chunk_documents(documents):
    """
    Split documents into smaller chunks before storing in vector DB.
    """

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,      # Ideal for company documents
        chunk_overlap=100    # Prevents losing boundary context
    )

    chunks = text_splitter.split_documents(documents)

    return chunks

# Add Documents to Vector Store
def add_documents_to_vectorstore(documents):
    """
    Chunk documents and store them in Chroma.
    """

    vectordb = get_vectorstore()

    #Chunk before embedding
    chunks = chunk_documents(documents)

    vectordb.add_documents(chunks)

