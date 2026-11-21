import pytest
from src.ingestion.models import LawChunk
from src.retrieval.bm25_search import BM25SearchEngine, tokenize_vietnamese
from src.retrieval.hybrid_search import HybridSearchEngine
from src.retrieval.models import SearchResult


def test_tokenize_vietnamese():
    text = "Điều 58: Điểm của giấy phép lái xe hạng A1 theo Luật 36/2024/QH15."
    tokens = tokenize_vietnamese(text)
    assert "điều" in tokens
    assert "58" in tokens
    assert "a1" in tokens
    assert "36/2024/qh15" in tokens


def test_bm25_search_engine():
    chunks = [
        LawChunk(
            id="dieu_1",
            document_id="doc1",
            law_number="36/2024",
            law_name="Luật",
            chapter_number=1,
            chapter_title="Chung",
            article_number=1,
            article_title="Phạm vi",
            clause_number=1,
            point=None,
            text="Điều 1. Phạm vi điều chỉnh của luật giao thông đường bộ.",
            raw_content="Phạm vi điều chỉnh của luật giao thông đường bộ.",
            references=[],
        ),
        LawChunk(
            id="dieu_58",
            document_id="doc1",
            law_number="36/2024",
            law_name="Luật",
            chapter_number=4,
            chapter_title="Người lái xe",
            article_number=58,
            article_title="Điểm giấy phép lái xe",
            clause_number=1,
            point=None,
            text="Điều 58. Điểm của giấy phép lái xe gồm 12 điểm mỗi năm.",
            raw_content="Điểm của giấy phép lái xe gồm 12 điểm mỗi năm.",
            references=[],
        ),
    ]

    engine = BM25SearchEngine()
    engine.build_index(chunks)

    results = engine.search("Điều 58 điểm giấy phép lái xe", top_k=2)
    assert len(results) > 0
    assert results[0].article_number == 58
    assert results[0].source_type == "bm25"


def test_rrf_scoring_combines_ranks():
    class DummyEngine:
        def __init__(self, results):
            self._res = results

        def search(self, query, top_k=10):
            return self._res

    item_a = SearchResult(
        chunk_id="c_a", score=10.0, rank=1,
        document_id="d", law_number="36", law_name="Luật",
        chapter_number=1, chapter_title="C", article_number=1, article_title="A",
        text="A", raw_content="A",
    )
    item_b = SearchResult(
        chunk_id="c_b", score=5.0, rank=2,
        document_id="d", law_number="36", law_name="Luật",
        chapter_number=1, chapter_title="C", article_number=2, article_title="B",
        text="B", raw_content="B",
    )

    bm25 = DummyEngine([item_a, item_b])
    vector = DummyEngine([item_b, item_a])

    hybrid = HybridSearchEngine(bm25_engine=bm25, vector_engine=vector, rrf_k=60)
    results = hybrid.search("query", top_k=2)

    assert len(results) == 2
    # Cả hai item đều xuất hiện ở rank 1 trong 1 bên và rank 2 trong bên kia -> điểm RRF bằng nhau: 1/(60+1) + 1/(60+2)
    assert results[0].score == results[1].score
