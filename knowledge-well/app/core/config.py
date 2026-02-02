
import os
from dataclasses import dataclass

# app/core/config.py
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())  # loads .env from project root if present


@dataclass
class Settings:
    # GraphDB
    GRAPHDB_BASE_URL: str = os.getenv("GRAPHDB_BASE_URL", "http://localhost:7200")
    GRAPHDB_REPOSITORY: str = os.getenv("GRAPHDB_REPOSITORY", "repo")
    GRAPHDB_AUTH: str = os.getenv("GRAPHDB_AUTH", "BASIC")  # "BASIC" or "GDB"
    GRAPHDB_USERNAME: str = os.getenv("GRAPHDB_USERNAME", "")
    GRAPHDB_PASSWORD: str = os.getenv("GRAPHDB_PASSWORD", "")
    GRAPHDB_VERIFY_TLS: bool = os.getenv("GRAPHDB_VERIFY_TLS", "true").lower() == "true"
    GRAPHDB_TIMEOUT: int = int(os.getenv("GRAPHDB_TIMEOUT", "30"))
    GRAPHDB_TOKEN_TTL_SECONDS: int = int(os.getenv("GRAPHDB_TOKEN_TTL_SECONDS", "36000"))

    # Vector store
    VECTORSTORE_PATH: str = os.getenv("RAG_VECTORSTORE_PATH", "./Vectorstore/chromadb")
    VECTOR_COLLECTION: str = os.getenv("RAG_VECTOR_COLLECTION", "documents")
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "800"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "120"))

    # Embeddings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    EMBED_BATCH: int = int(os.getenv("EMBED_BATCH", "32"))
    DEVICE: str = os.getenv("DEVICE", "cpu")

    # LLM (Ollama)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

    # app/core/config.py (inside Settings)
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_BASE_URL: str | None = os.getenv("OPENAI_BASE_URL")  # usually leave unset
    OPENAI_TIMEOUT_SECONDS: int = int(os.getenv("OPENAI_TIMEOUT_SECONDS", "600"))
    OPENAI_USE_RESPONSES: bool = os.getenv("OPENAI_USE_RESPONSES", "true").lower() == "true"

    #Gemini config
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    GEMINI_TIMEOUT_SECONDS: int = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "600"))

    #Query Rewriter Agent Config
    USE_LLM_REWRITER: bool = (os.getenv("USE_LLM_REWRITER", "true").lower() == "true")
    REWRITER_PROVIDER: str = os.getenv("REWRITER_PROVIDER", "OPENAI")
    REWRITER_MODEL: str = os.getenv("REWRITER_MODEL", "gpt-4o-mini")
    REWRITER_TIMEOUT_SECONDS: int = int(os.getenv("REWRITER_TIMEOUT_SECONDS", "45"))

    # Switch between LLMs
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "OLLAMA")  # or "OPENAI"

    # API
    PORT: int = int(os.getenv("PORT", "8000"))

settings = Settings()
# Query rewriter
USE_LLM_REWRITER: bool = (os.getenv("USE_LLM_REWRITER", "true").lower() == "true")

