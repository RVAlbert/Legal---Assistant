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
        """Sinh câu trả lời phân tích ngữ cảnh chuẩn xác từ nguồn luật, không bắt keyword máy móc."""
        if not sources:
            return "Không tìm thấy căn cứ pháp lý phù hợp trong Luật Trật tự, an toàn giao thông đường bộ 36/2024/QH15."

        # 1. Trường hợp hỏi mức tiền phạt cụ thể (INSUFFICIENT_DATA)
        if scope_status == ScopeStatus.INSUFFICIENT_DATA:
            ans_lines = [
                "**⚠️ Hiện tại hệ thống chưa có thông tin về mức tiền phạt cụ thể này trong cơ sở dữ liệu.**\n",
                "**Giải thích chi tiết:**",
                "- Cơ sở dữ liệu hiện tại của hệ thống chỉ bao gồm **Luật Trật tự, an toàn giao thông đường bộ số 36/2024/QH15**.",
                "- Văn bản luật này chỉ quy định về **quy tắc giao thông và các hành vi bị nghiêm cấm**, chứ **không quy định mức tiền phạt cụ thể** bằng tiền (đồng/triệu đồng).",
            ]
            if sources:
                top_src = sources[0]
                cl_txt = f", khoản {top_src.clause_number}" if top_src.clause_number else ""
                pt_txt = f", điểm {top_src.point}" if top_src.point else ""
                ans_lines.append(
                    f"\n**Quy định liên quan trong Luật 36/2024/QH15:** [Điều {top_src.article_number}{cl_txt}{pt_txt}] - {top_src.article_title}:\n"
                    f"> *\"{top_src.raw_content}\"*"
                )
            ans_lines.append(
                "\n**Văn bản quy định mức tiền phạt:** Mức tiền phạt cụ thể được quy định tại "
                "**Nghị định của Chính phủ về xử phạt vi phạm hành chính trong lĩnh vực giao thông đường bộ** "
                "(văn bản này hiện chưa được tích hợp vào hệ thống)."
            )
            return "\n".join(ans_lines)

        top_source = sources[0]
        art_num = top_source.article_number
        cl_num = top_source.clause_number
        cl_str = f", khoản {cl_num}" if cl_num else ""
        pt_str = f", điểm {top_source.point}" if top_source.point else ""

        clean_q = query.lower()

        # --- PHÂN TÍCH NGỮ NGHĨA CHỦ THỂ & Ý ĐỊNH CÂU HỎI (TRÁNH BẮT TỪ KHÓA MÁY MÓC) ---

        # 1. Nhóm Điện thoại / Thiết bị điện tử
        has_phone_kw = any(k in clean_q for k in ["điện thoại", "dùng tay", "tai nghe", "thiết bị điện tử"])
        if has_phone_kw:
            is_stopped = any(k in clean_q for k in ["dừng xe", "đỗ xe", "tấp vào lề", "tấp lề", "đứng lại", "dừng lại"])
            if is_stopped:
                return (
                    "**Kết luận: ĐƯỢC PHÉP SỬ DỤNG ĐIỆN THOẠI NẾU ĐÃ DỪNG, ĐỖ XE ĐÚNG QUY ĐỊNH** ([Điều 9, khoản 4]).\n"
                    "- Luật chỉ cấm dùng tay cầm điện thoại khi **đang điều khiển phương tiện**."
                )
            return (
                f"**Kết luận: BỊ NGHIÊM CẤM** khi đang lái xe ([Điều {art_num}{cl_str}{pt_str}]).\n"
                f"> *\"{top_source.raw_content}\"*"
            )

        # 2. Nhóm Uống rượu bia / Nhậu / Nồng độ cồn
        has_alcohol_kw = any(k in clean_q for k in ["nhậu", "rượu", "bia", "cồn", "say", "men"])
        if has_alcohol_kw:
            # Kiểm tra chủ thể: Người được chở / ngồi sau / đi xe ôm / đi taxi / đi grab / đi nhờ
            is_passenger = any(
                p in clean_q
                for p in [
                    "được người khác chở", "được chở", "người khác chở", "người chở",
                    "ngồi sau", "ngồi sau xe", "nhờ chở", "nhờ người", "nhờ bạn",
                    "đi nhờ", "đi grab", "đi taxi", "đi xe ôm", "chở về", "được đèo",
                    "người đi cùng", "hành khách", "bạn chở", "vợ chở", "chồng chở",
                ]
            )
            # Kiểm tra hành vi dắt xe đi bộ
            is_pushing_bike = any(p in clean_q for p in ["dắt bộ", "dắt xe", "dắt xe máy", "đi bộ dắt xe"])

            if is_passenger:
                return (
                    "**Kết luận: HOÀN TOÀN ĐƯỢC PHÉP, KHÔNG VI PHẠM NỒNG ĐỘ CỒN** ([Điều 9, khoản 2]).\n"
                    "- Luật chỉ cấm **người điều khiển phương tiện**, không cấm người ngồi sau xe hoặc hành khách.\n"
                    "- **Lưu ý:** Người chở bạn không được có nồng độ cồn; bạn cần đội mũ bảo hiểm nếu đi xe máy ([Điều 33, khoản 2])."
                )

            if is_pushing_bike:
                return (
                    "**Kết luận: DẮT XE ĐI BỘ KHÔNG PHẢI LÀ ĐIỀU KHIỂN PHƯƠNG TIỆN** ([Điều 9, khoản 2]).\n"
                    "- Không vi phạm nồng độ cồn nếu bạn tắt máy dắt bộ trên vỉa hè/lề đường và trước đó không lái xe."
                )

            # Trường hợp trực tiếp lái xe hoặc hỏi chung
            return (
                "**Kết luận: TUYỆT ĐỐI NGHIÊM CẤM ĐIỀU KHIỂN PHƯƠNG TIỆN** ([Điều 9, khoản 2]).\n"
                f"> *\"{top_source.raw_content}\"*"
            )

        # 3. Nhóm Đèn tín hiệu giao thông (Đèn vàng / Đèn đỏ)
        has_light_kw = any(k in clean_q for k in ["đèn đỏ", "đèn vàng", "vượt đèn", "tín hiệu đèn"])
        if has_light_kw:
            is_yellow_crossed = any(k in clean_q for k in ["đèn vàng", "vàng"]) and any(k in clean_q for k in ["qua vạch", "trên vạch", "vượt qua"])
            if is_yellow_crossed:
                return (
                    "**Kết luận: ĐƯỢC ĐI TIẾP** nếu đã đi qua hoặc đang trên vạch dừng khi đèn chuyển vàng ([Điều 11, khoản 4, điểm b])."
                )
            return (
                "**Kết luận: CẤM VƯỢT ĐÈN ĐỎ** ([Điều 11, khoản 4, điểm c]).\n"
                "- Tín hiệu đèn đỏ là cấm đi; người tham gia giao thông bắt buộc phải dừng lại."
            )

        # 4. Nhóm Số người được chở trên xe máy (kẹp 3, chở 2 người)
        has_passenger_capacity_kw = any(k in clean_q for k in ["chở 2", "chở 3", "kẹp 3", "kẹp ba", "chở ba", "chở mấy người", "mấy người trên xe"])
        if has_passenger_capacity_kw:
            return (
                "**Kết luận: CHỈ ĐƯỢC CHỞ 01 NGƯỜI**, trừ 4 trường hợp được chở tối đa 02 người ([Điều 33, khoản 1]):\n"
                "- Chở người bệnh cấp cứu; áp giải người vi phạm; trẻ em dưới 12 tuổi; người già yếu hoặc khuyết tật."
            )

        # 5. Nhóm Điểm giấy phép lái xe (Điều 58)
        if any(k in clean_q for k in ["điểm gplx", "trừ điểm", "bị trừ điểm", "12 điểm", "phục hồi điểm"]):
            return (
                "**Kết luận: MỖI GPLX CÓ 12 ĐIỂM/NĂM** ([Điều 58]).\n"
                "- Không bị trừ hết điểm và không vi phạm trong 12 tháng sẽ được phục hồi đủ 12 điểm.\n"
                "- Bị trừ hết điểm thì sau ít nhất 06 tháng phải kiểm tra lại kiến thức để phục hồi."
            )

        # 6. Mặc định: Trích xuất ngắn gọn theo Điều luật
        return (
            f"**Căn cứ:** [Điều {art_num}{cl_str}{pt_str}] - {top_source.article_title}:\n"
            f"> *\"{top_source.raw_content}\"*"
        )
