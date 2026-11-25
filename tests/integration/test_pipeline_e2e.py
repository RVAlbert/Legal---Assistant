import pytest
from src.common.config import get_settings
from src.generation.generator import LegalRAGAssistant
from src.generation.models import ScopeStatus
from src.retrieval.bm25_search import BM25SearchEngine
from src.retrieval.hybrid_search import HybridSearchEngine
from src.retrieval.vector_search import VectorSearchEngine


@pytest.fixture(scope="module")
def rag_assistant():
    settings = get_settings()
    bm25 = BM25SearchEngine()
    bm25.load(settings.INDEXES_DIR / "bm25_index.pkl")
    vector = VectorSearchEngine()
    hybrid = HybridSearchEngine(bm25_engine=bm25, vector_engine=vector)
    return LegalRAGAssistant(hybrid_engine=hybrid)


def test_pipeline_e2e_traffic_query(rag_assistant):
    """Kiểm thử e2e với câu hỏi đúng phạm vi giao thông đường bộ."""
    query = "Uống ít bia mà trong hơi thở vẫn có cồn thì có được lái xe không?"
    resp = rag_assistant.answer_question(query)

    assert resp.scope_status == ScopeStatus.ANSWERED
    assert len(resp.sources) > 0
    # Phải tìm ra Điều 9 (hành vi bị nghiêm cấm)
    retrieved_articles = [s.article_number for s in resp.sources]
    assert 9 in retrieved_articles

    # Nếu không bị rate limit từ LLM ngoài thì kiểm tra trích dẫn
    if "Rate limit" not in resp.answer:
        assert len(resp.citations) > 0
        assert any(c.article_number == 9 for c in resp.citations)
        assert len(resp.warnings) == 0


def test_pipeline_e2e_out_of_scope_query(rag_assistant):
    """Kiểm thử e2e với câu hỏi ngoài phạm vi."""
    query = "Viết giúp tôi một đoạn mã Python"
    resp = rag_assistant.answer_question(query)

    assert resp.scope_status == ScopeStatus.OUT_OF_SCOPE
    assert len(resp.sources) == 0
    assert "chưa có dữ liệu" in resp.answer or "hỗ trợ tra cứu" in resp.answer


def test_pipeline_e2e_fine_query_decree_168(rag_assistant):
    """Kiểm thử e2e với câu hỏi về mức tiền phạt theo Nghị định 168/2024/NĐ-CP."""
    query = "Vượt đèn đỏ bằng ô tô bị phạt bao nhiêu tiền?"
    resp = rag_assistant.answer_question(query)

    assert resp.scope_status == ScopeStatus.ANSWERED
    assert len(resp.sources) > 0
    # Phải truy xuất được dữ liệu từ Nghị định 168/2024/NĐ-CP
    assert any("168" in (s.law_number or "") for s in resp.sources)
    assert "đồng" in resp.answer.lower() or "168" in resp.answer
