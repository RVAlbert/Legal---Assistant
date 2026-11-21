import time
from typing import Optional
from src.common.config import get_settings
from src.common.logger import get_logger
from src.generation.citation_validator import CitationValidator
from src.generation.context_builder import ContextBuilder
from src.generation.cross_ref_expander import CrossReferenceExpander
from src.generation.llm_client import OpenRouterLLMClient
from src.generation.models import GenerationResponse, ScopeStatus
from src.generation.scope_validator import ScopeValidator
from src.retrieval.hybrid_search import HybridSearchEngine

logger = get_logger("generator")


class LegalRAGAssistant:
    """Bộ trợ lý hỏi đáp pháp luật toàn diện (Bước 15).

    Tích hợp toàn bộ quy trình:
    1. Kiểm tra phạm vi (Scope Validator).
    2. Tìm kiếm lai BM25 + Qdrant (Hybrid Search).
    3. Mở rộng tham chiếu chéo (Cross-reference Expansion).
    4. Lắp ráp ngữ cảnh và quy tắc (Context Builder).
    5. Gọi OpenRouter LLM (NVIDIA Nemotron 3 Ultra hoặc model cấu hình).
    6. Kiểm tra tính xác thực của trích dẫn (Citation Validator).
    """

    def __init__(
        self,
        hybrid_engine: HybridSearchEngine,
        llm_client: Optional[OpenRouterLLMClient] = None,
        top_k: int = 5,
    ):
        self.hybrid_engine = hybrid_engine
        self.llm_client = llm_client or OpenRouterLLMClient()
        self.scope_validator = ScopeValidator()
        self.expander = CrossReferenceExpander(vector_engine=hybrid_engine.vector_engine)
        self.context_builder = ContextBuilder()
        self.citation_validator = CitationValidator()
        self.top_k = top_k

    def answer_question(self, query: str) -> GenerationResponse:
        start_time = time.time()
        logger.info(f"Tiếp nhận câu hỏi: \"{query}\"")

        # 1. Đánh giá nhanh trước tìm kiếm (Pre-retrieval scope check)
        pre_check = self.scope_validator.assess_pre_retrieval(query)
        if pre_check and pre_check.status == ScopeStatus.OUT_OF_SCOPE:
            latency = (time.time() - start_time) * 1000
            return GenerationResponse(
                query=query,
                scope_status=ScopeStatus.OUT_OF_SCOPE,
                answer=pre_check.reason,
                citations=[],
                sources=[],
                expansion_sources=[],
                warnings=[],
                latency_ms=round(latency, 1),
            )

        # 2. Tìm kiếm tài liệu bằng Hybrid Search
        search_results = self.hybrid_engine.search(query, top_k=self.top_k)

        # 3. Đánh giá phạm vi sau tìm kiếm (Post-retrieval scope check)
        post_check = self.scope_validator.assess_post_retrieval(query, search_results)
        if post_check.status == ScopeStatus.OUT_OF_SCOPE:
            latency = (time.time() - start_time) * 1000
            return GenerationResponse(
                query=query,
                scope_status=ScopeStatus.OUT_OF_SCOPE,
                answer=post_check.reason,
                citations=[],
                sources=[],
                expansion_sources=[],
                warnings=[],
                latency_ms=round(latency, 1),
            )

        # 4. Mở rộng tham chiếu chéo nếu có
        expansion_sources = self.expander.expand(search_results)

        # 5. Xây dựng prompt ngữ cảnh
        messages = self.context_builder.build_prompt(
            query=query,
            primary_sources=search_results,
            expansion_sources=expansion_sources,
            scope_status=post_check.status,
            scope_note=post_check.reason if post_check.status == ScopeStatus.INSUFFICIENT_DATA else "",
        )

        # 6. Gọi LLM OpenRouter
        llm_answer = self.llm_client.generate(messages=messages)

        # 7. Kiểm tra tính hợp lệ của trích dẫn
        all_available_sources = search_results + expansion_sources
        citations, warnings = self.citation_validator.validate_citations(
            answer_text=llm_answer,
            available_sources=all_available_sources,
        )

        latency = (time.time() - start_time) * 1000
        return GenerationResponse(
            query=query,
            scope_status=post_check.status,
            answer=llm_answer,
            citations=citations,
            sources=search_results,
            expansion_sources=expansion_sources,
            warnings=warnings,
            latency_ms=round(latency, 1),
        )
