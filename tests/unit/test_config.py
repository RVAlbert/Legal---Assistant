import pytest
from src.common.config import get_settings, Settings


def test_settings_load_defaults():
    settings = get_settings()
    assert settings.APP_ENV in ["development", "production", "testing"]
    assert settings.OPENROUTER_MODEL == "nvidia/nemotron-3-ultra-550b-a55b:free"
    assert settings.OPENROUTER_BASE_URL == "https://openrouter.ai/api/v1"
    assert settings.QDRANT_COLLECTION == "law_chunks"
    assert settings.EMBEDDING_MODEL == "BAAI/bge-m3"
    assert settings.RETRIEVAL_TOP_K == 8
    assert settings.CONTEXT_TOP_K == 5


def test_settings_paths_exist():
    settings = get_settings()
    assert settings.BASE_DIR.exists()
    assert settings.INPUT_DIR.exists()
    assert (settings.INPUT_DIR / "luat_giao_thong_2024_clean.docx").exists()
