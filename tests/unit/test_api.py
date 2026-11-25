import pytest
from fastapi.testclient import TestClient
from src.api.app import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "VN Legal" in data["app_name"]
    assert data["total_indexed_chunks"] >= 500


def test_documents_endpoint(client):
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert data["law_number"] == "36/2024/QH15"
    assert data["total_chapters"] == 9
    assert data["total_articles"] == 89


def test_search_endpoint(client):
    response = client.post(
        "/api/v1/search",
        json={"query": "Điều 58 điểm giấy phép lái xe", "top_k": 3},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] > 0
    top_art = data["results"][0]["article_number"]
    assert top_art == 58


def test_chat_endpoint_out_of_scope(client):
    # Test câu hỏi ngoài phạm vi không cần gọi LLM (tốc độ cao và không tốn quota)
    response = client.post(
        "/api/v1/chat",
        json={"query": "Thử việc theo Luật Lao động là bao lâu?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["scope_status"] == "out_of_scope"
    assert "Luật Lao động" in data["answer"] or "luật lao động" in data["answer"]
