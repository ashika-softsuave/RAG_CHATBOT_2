import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHROMA_PATH = "data/chroma"
UPLOAD_DIR = "data/uploads"
ADMIN_EMAIL = "abi956705@gmail.com"
