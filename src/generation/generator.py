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

    def answer_question(
        self,
        query: str,
        chat_history: Optional[list] = None,
    ) -> GenerationResponse:
        start_time = time.time()
        logger.info(f"Tiếp nhận câu hỏi: \"{query}\"")

        # 1. Đánh giá nhanh trước tìm kiếm (Pre-retrieval: giao tiếp xã hội, lạc đề/ghẹo chọc, ngoài phạm vi)
        pre_check = self.scope_validator.assess_pre_retrieval(query)
        if pre_check:
            latency = (time.time() - start_time) * 1000
            return GenerationResponse(
                query=query,
                scope_status=pre_check.status,
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

        # 5. Xây dựng prompt ngữ cảnh (có kèm lịch sử hội thoại gần nhất để hiểu câu hỏi nối tiếp)
        messages = self.context_builder.build_prompt(
            query=query,
            primary_sources=search_results,
            expansion_sources=expansion_sources,
            scope_status=post_check.status,
            scope_note=post_check.reason if post_check.status == ScopeStatus.INSUFFICIENT_DATA else "",
            chat_history=chat_history,
        )

        # 6. Gọi LLM OpenRouter
        llm_answer = self.llm_client.generate(messages=messages)

        # Nếu LLM gặp lỗi (ví dụ Rate Limit 429 hoặc sự cố kết nối), tự động sinh câu trả lời trích xuất chuẩn xác từ nguồn
        if not llm_answer or "Rate limit" in llm_answer or "Dịch vụ mô hình" in llm_answer or llm_answer.startswith("⚠️"):
            logger.info("Chuyển sang chế độ extractive fallback dựa trên nguồn luật chuẩn.")
            llm_answer = self._generate_extractive_fallback(
                query=query,
                sources=search_results,
                scope_status=post_check.status,
            )

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

    def _generate_extractive_fallback(
        self,
        query: str,
        sources: list,
        scope_status: ScopeStatus,
    ) -> str:
        """Fallback an toàn khi dịch vụ AI tạm thời không phản hồi: KHÔNG gán cứng từ khóa, KHÔNG trả lời lặp."""
        if not sources:
            return (
                "Hiện tại dữ liệu của hệ thống không có quy định cho câu hỏi này "
                "(hoặc nội dung nằm ngoài phạm vi Luật 36/2024/QH15 và Nghị định 168/2024/NĐ-CP)."
            )

        if scope_status == ScopeStatus.INSUFFICIENT_DATA:
            return (
                "Hiện tại dữ liệu của hệ thống chưa có thông tin chi tiết cho nội dung bạn đang hỏi "
                "(nằm ngoài dữ liệu văn bản pháp luật hiện có)."
            )

        top_source = sources[0]
        doc_tag = (
            "Nghị định 168/2024/NĐ-CP"
            if "168" in (top_source.law_number or "")
            else f"Luật {top_source.law_number}"
        )
        cl_str = f", khoản {top_source.clause_number}" if top_source.clause_number else ""
        pt_str = f", điểm {top_source.point}" if top_source.point else ""

        return (
            f"Hệ thống AI phân tích đang bận tạm thời. Dưới đây là điều khoản gần nhất tìm thấy trong dữ liệu:\n\n"
            f"**[{doc_tag}, Điều {top_source.article_number}{cl_str}{pt_str}]** — {top_source.article_title}:\n"
            f"> *\"{top_source.raw_content}\"*\n\n"
            "*(Nếu nội dung trên chưa đúng câu hỏi của bạn, có thể quy định này chưa có trong dữ liệu hiện tại hoặc bạn hãy thử hỏi lại sau vài giây để AI phân tích trực tiếp.)*"
        )
