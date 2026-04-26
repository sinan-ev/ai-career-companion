import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER  = os.getenv("LLM_PROVIDER", "openai")
LLM_MODEL     = os.getenv("LLM_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")

EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "auto")
VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", "./data/vector_store")
UPLOAD_DIR        = os.getenv("UPLOAD_DIR", "./data/uploads")
MAX_ROWS_PREVIEW  = 1000
