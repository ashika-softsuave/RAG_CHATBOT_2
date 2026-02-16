from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from app.core.config import CHROMA_PATH

embeddings = OpenAIEmbeddings()

def get_vectorstore():
    return Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings
    )
