from typing import Optional
from fastapi import APIRouter, HTTPException
from src.api.schemas import (
    ChatRequest,
    ChatResponse,
    DocumentInfo,
    HealthResponse,
    SearchRequest,
    SearchResponse,
)
from src.common.config import get_settings
from src.generation.generator import LegalRAGAssistant
from src.retrieval.bm25_search import BM25SearchEngine
from src.retrieval.hybrid_search import HybridSearchEngine
from src.retrieval.vector_search import VectorSearchEngine

router = APIRouter()

# Biến toàn cục quản lý các engine (được khởi tạo khi startup)
_hybrid_engine: Optional[HybridSearchEngine] = None
_assistant: Optional[LegalRAGAssistant] = None


def get_assistant() -> LegalRAGAssistant:
    global _assistant, _hybrid_engine
    if _assistant is None:
        settings = get_settings()
        bm25_file = settings.INDEXES_DIR / "bm25_index.pkl"

        bm25 = BM25SearchEngine()
        if bm25_file.exists():
            bm25.load(bm25_file)
        else:
            raise RuntimeError(f"Chưa có BM25 index tại {bm25_file}. Hãy chạy build_indexes trước.")

        vector = VectorSearchEngine()
        _hybrid_engine = HybridSearchEngine(bm25_engine=bm25, vector_engine=vector)
        _assistant = LegalRAGAssistant(hybrid_engine=_hybrid_engine)
    return _assistant


def get_hybrid_engine() -> HybridSearchEngine:
    global _hybrid_engine
    if _hybrid_engine is None:
        get_assistant()
    return _hybrid_engine


@router.get("/health", response_model=HealthResponse)
def health_check():
    """Kiểm tra sức khỏe hệ thống và thông tin model."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        app_name=settings.OPENROUTER_APP_NAME,
        llm_model=settings.OPENROUTER_MODEL,
        embedding_model=settings.EMBEDDING_MODEL,
        total_indexed_chunks=500,
    )


@router.get("/api/v1/documents", response_model=DocumentInfo)
def get_documents_info():
    """Trả về thông tin văn bản pháp luật được hỗ trợ trong hệ thống."""
    return DocumentInfo(
        document_id="luat_trat_tu_an_toan_giao_thong_36_2024",
        law_name="Luật Trật tự, an toàn giao thông đường bộ",
        law_number="36/2024/QH15",
        issue_date="27/06/2024",
        effective_date="01/01/2025",
        total_chapters=9,
        total_articles=89,
        scope_description=(
            "Quy tắc giao thông, phương tiện, người tham gia giao thông, GPLX, điểm GPLX, "
            "tuần tra kiểm soát, giải quyết TNGT và quản lý nhà nước."
        ),
    )


@router.post("/api/v1/search", response_model=SearchResponse)
def search_law(request: SearchRequest):
    """Tìm kiếm trực tiếp các điều khoản luật liên quan bằng Hybrid Search (BM25 + BGE-M3 + RRF)."""
    try:
        engine = get_hybrid_engine()
        results = engine.search(query=request.query, top_k=request.top_k)
        return SearchResponse(
            query=request.query,
            total_results=len(results),
            results=results,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/chat", response_model=ChatResponse)
def chat_with_legal_assistant(request: ChatRequest):
    """Hỏi đáp pháp luật: Scope check -> Hybrid Retrieval -> OpenRouter LLM -> Citation Validation."""
    try:
        assistant = get_assistant()
        resp = assistant.answer_question(query=request.query)
        return ChatResponse(
            query=resp.query,
            scope_status=resp.scope_status,
            answer=resp.answer,
            citations=resp.citations,
            sources=resp.sources,
            expansion_sources=resp.expansion_sources,
            warnings=resp.warnings,
            latency_ms=resp.latency_ms,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
