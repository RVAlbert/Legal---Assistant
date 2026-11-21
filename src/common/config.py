from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Đường dẫn gốc của project
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Cấu hình ứng dụng VN Legal RAG Assistant."""

    # Môi trường
    APP_ENV: str = "development"

    # OpenRouter LLM
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "nvidia/nemotron-3-ultra-550b-a55b:free"
    OPENROUTER_SITE_URL: str = ""
    OPENROUTER_APP_NAME: str = "VN Legal RAG Assistant"

    # Qdrant Vector DB
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "law_chunks"

    # Embedding & Retrieval
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    RETRIEVAL_TOP_K: int = 8
    CONTEXT_TOP_K: int = 5

    # Thư mục dữ liệu
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    INPUT_DIR: Path = BASE_DIR / "data" / "input"
    PROCESSED_DIR: Path = BASE_DIR / "data" / "processed"
    INDEXES_DIR: Path = BASE_DIR / "data" / "indexes"
    EVALUATION_DIR: Path = BASE_DIR / "data" / "evaluation"
    LOGS_DIR: Path = BASE_DIR / "logs"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Trả về singleton instance của cấu hình."""
    return Settings()
