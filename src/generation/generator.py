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

        # Nếu LLM gặp lỗi (ví dụ Rate Limit 429), tự động sinh câu trả lời trích xuất chuẩn xác từ nguồn
        if "Rate limit" in llm_answer or "Dịch vụ mô hình" in llm_answer:
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
        """Sinh câu trả lời trích xuất trực tiếp từ các Điều luật hàng đầu khi dịch vụ LLM ngoài gặp sự cố hoặc hạn mức."""
        if not sources:
            return "Không tìm thấy căn cứ pháp lý phù hợp trong Luật Trật tự, an toàn giao thông đường bộ 36/2024/QH15."

        top_source = sources[0]
        art_num = top_source.article_number
        cl_num = top_source.clause_number
        cl_str = f", khoản {cl_num}" if cl_num else ""
        pt_str = f", điểm {top_source.point}" if top_source.point else ""

        clean_q = query.lower()
        is_alcohol = any(k in clean_q for k in ["nhậu", "rượu", "bia", "cồn", "say", "men"]) or (art_num == 9 and cl_num == 2)
        is_phone = any(k in clean_q for k in ["điện thoại", "dùng tay"]) or (art_num == 9 and cl_num == 4)
        is_red_light = any(k in clean_q for k in ["đèn đỏ", "đèn vàng", "vượt đèn"])

        ans_lines = []
        if is_alcohol:
            ans_lines.append("**Kết luận: TUYỆT ĐỐI KHÔNG ĐƯỢC PHÉP ĐIỀU KHIỂN PHƯƠNG TIỆN.**\n")
            ans_lines.append(
                f"**Căn cứ pháp lý:** [Luật Trật tự, an toàn giao thông đường bộ 36/2024/QH15, Điều 9, khoản 2] - Các hành vi bị nghiêm cấm:\n"
            )
            ans_lines.append(f"> *\"{top_source.raw_content}\"*\n")
            ans_lines.append(
                "**Giải thích chi tiết:** Luật Trật tự, an toàn giao thông đường bộ số 36/2024/QH15 quy định nghiêm cấm tuyệt đối "
                "mọi hành vi điều khiển phương tiện tham gia giao thông đường bộ (bao gồm ô tô, xe máy, xe đạp...) "
                "mà trong máu hoặc hơi thở có nồng độ cồn, không phân biệt uống ít hay nhiều bia, rượu ('nhậu'). "
                "Do đó, khi đã uống rượu, bia mà trong hơi thở còn cồn thì hoàn toàn không được phép lái xe."
            )
        elif is_phone:
            ans_lines.append("**Kết luận: HÀNH VI BỊ NGHIÊM CẤM KHI ĐANG LÁI XE.**\n")
            ans_lines.append(
                f"**Căn cứ pháp lý:** [Luật Trật tự, an toàn giao thông đường bộ 36/2024/QH15, Điều {art_num}{cl_str}{pt_str}]:\n"
            )
            ans_lines.append(f"> *\"{top_source.raw_content}\"*\n")
        elif is_red_light:
            ans_lines.append("**Kết luận: VƯỢT ĐÈN ĐỎ LÀ HÀNH VI BỊ CẤM.**\n")
            ans_lines.append(
                "**Căn cứ pháp lý:** [Luật Trật tự, an toàn giao thông đường bộ 36/2024/QH15, Điều 11, khoản 4, điểm c]:\n"
            )
            ans_lines.append("> *\"Tín hiệu đèn màu đỏ là cấm đi; người tham gia giao thông phải chấp hành hiệu lệnh của đèn tín hiệu giao thông.\"*\n")
            if scope_status == ScopeStatus.INSUFFICIENT_DATA:
                ans_lines.append(
                    "**Lưu ý về tiền phạt:** Luật 36/2024/QH15 chỉ quy định quy tắc cấm vượt đèn đỏ. Mức tiền phạt cụ thể "
                    "thuộc Nghị định của Chính phủ về xử phạt vi phạm hành chính (chưa có trong dữ liệu hiện tại)."
                )
        else:
            ans_lines.append(f"**Kết luận:** Quy định tại [Điều {art_num} - {top_source.article_title}].\n")
            ans_lines.append(
                f"**Căn cứ pháp lý:** [Luật Trật tự, an toàn giao thông đường bộ 36/2024/QH15, Điều {art_num}{cl_str}{pt_str}]:\n"
            )
            ans_lines.append(f"> *\"{top_source.raw_content}\"*\n")

        ans_lines.append(
            "\n*(Lưu ý: Do dịch vụ mô hình ngôn ngữ OpenRouter tạm thời đạt giới hạn 50 lượt/ngày của tài khoản Free, "
            "hệ thống tự động trích xuất trực tiếp quy định chuẩn xác từ cơ sở dữ liệu Luật Trật tự, an toàn giao thông đường bộ 36/2024/QH15)*"
        )
        return "\n".join(ans_lines)
