# backend/config.py
import os
from enum import Enum
from pydantic_settings import BaseSettings
from functools import lru_cache

class LLMProvider(str, Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"

class EmbeddingProvider(str, Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"
    VOYAGE = "voyage"

class ChunkingStrategy(str, Enum):
    FIXED = "fixed"
    SEMANTIC = "semantic"
    RECURSIVE = "recursive"

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "PDF-to-Agent"
    DEBUG: bool = False

    # LLM Configuration
    DEFAULT_LLM_PROVIDER: LLMProvider = LLMProvider.OLLAMA
    DEFAULT_EMBEDDING_PROVIDER: EmbeddingProvider = EmbeddingProvider.OLLAMA

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_TEMPERATURE: float = 0.3
    OPENAI_MAX_TOKENS: int = 2000

    # Ollama (local)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    OLLAMA_TEMPERATURE: float = 0.3
    OLLAMA_NUM_CTX: int = 4096

    # Anthropic
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

    # Vector Store
    VECTOR_STORE_TYPE: str = "faiss"  # or "chroma", "pinecone"

    # Document Processing
    CHUNKING_STRATEGY: ChunkingStrategy = ChunkingStrategy.RECURSIVE
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_FILE_TYPES: list = [".pdf"]

    # Multi-doc settings
    MAX_DOCUMENTS_PER_SESSION: int = 100
    MAX_CHUNKS_PER_QUERY: int = 10
    TOP_K_PER_DOCUMENT: int = 3
    ENABLE_CROSS_DOC_SEARCH: bool = True

    # Vector Search
    SIMILARITY_THRESHOLD: float = 0.7

    # Storage
    STORAGE_DIR: str = "./storage"
    VECTOR_STORE_DIR: str = "./storage/vector_store"
    DOCUMENTS_DIR: str = "./storage/documents"
    METADATA_DIR: str = "./storage/metadata"
    MEMORY_DIR: str = "./storage/memory"

    # Session
    SESSION_EXPIRY_HOURS: int = 24

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

# Initialize settings and create directories
settings = get_settings()

for dir_path in [
    settings.STORAGE_DIR,
    settings.VECTOR_STORE_DIR,
    settings.DOCUMENTS_DIR,
    settings.METADATA_DIR,
    settings.MEMORY_DIR
]:
    os.makedirs(dir_path, exist_ok=True)