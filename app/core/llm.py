from app.core.config import OPENAI_API_KEY
from langchain_openai import ChatOpenAI

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not found in environment")

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.2,
    openai_api_key=OPENAI_API_KEY
)
