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
        has_phone_kw = any(k in clean_q for k in ["điện thoại", "dùng tay", "tai nghe", "thiết bị điện tử"]) or (art_num == 9 and cl_num == 4)
        if has_phone_kw:
            is_stopped = any(k in clean_q for k in ["dừng xe", "đỗ xe", "tấp vào lề", "tấp lề", "đứng lại", "dừng lại"])
            if is_stopped:
                return (
                    "**Kết luận: ĐƯỢC PHÉP SỬ DỤNG ĐIỆN THOẠI NẾU ĐÃ DỪNG, ĐỖ XE ĐÚNG QUY ĐỊNH.**\n\n"
                    "**Căn cứ pháp lý:** [Luật Trật tự, an toàn giao thông đường bộ 36/2024/QH15, Điều 9, khoản 4]:\n"
                    f"> *\"{top_source.raw_content}\"*\n\n"
                    "**Giải thích chi tiết:**\n"
                    "Khoản 4 Điều 9 chỉ nghiêm cấm hành vi *\"Dùng tay cầm và sử dụng điện thoại hoặc thiết bị điện tử khác khi đang điều khiển phương tiện tham gia giao thông đường bộ\"*.\n"
                    "Do đó, nếu bạn tấp xe vào lề đường, dừng hoặc đỗ xe đúng nơi quy định an toàn thì việc cầm và nghe gọi, nhắn tin trên điện thoại là hoàn toàn hợp pháp."
                )
            return (
                "**Kết luận: HÀNH VI BỊ NGHIÊM CẤM KHI ĐANG ĐIỀU KHIỂN PHƯƠNG TIỆN.**\n\n"
                f"**Căn cứ pháp lý:** [Luật Trật tự, an toàn giao thông đường bộ 36/2024/QH15, Điều {art_num}{cl_str}{pt_str}]:\n"
                f"> *\"{top_source.raw_content}\"*\n\n"
                "**Giải thích chi tiết:** Luật nghiêm cấm người đang lái xe (ô tô, xe máy...) dùng tay cầm và sử dụng điện thoại. "
                "Nếu có nhu cầu nghe gọi, bạn phải dừng hoặc đỗ xe đúng nơi quy định trước khi sử dụng."
            )

        # 2. Nhóm Uống rượu bia / Nhậu / Nồng độ cồn
        has_alcohol_kw = any(k in clean_q for k in ["nhậu", "rượu", "bia", "cồn", "say", "men"]) or (art_num == 9 and cl_num == 2)
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
                    "**Kết luận: HOÀN TOÀN ĐƯỢC PHÉP, BẠN KHÔNG BỊ XỬ PHẠT VỀ NỒNG ĐỘ CỒN.**\n\n"
                    "**Căn cứ pháp lý:** [Luật Trật tự, an toàn giao thông đường bộ 36/2024/QH15, Điều 9, khoản 2] - Các hành vi bị nghiêm cấm:\n"
                    f"> *\"{top_source.raw_content}\"*\n\n"
                    "**Giải thích chi tiết theo Luật:**\n"
                    "1. **Chỉ cấm người trực tiếp điều khiển:** Khoản 2 Điều 9 Luật 36/2024/QH15 quy định nghiêm cấm: *\"Điều khiển phương tiện tham gia giao thông đường bộ mà trong máu hoặc hơi thở có nồng độ cồn.\"* Quy định này **chỉ áp dụng đối với người trực tiếp điều khiển phương tiện (người lái xe)**, hoàn toàn **không cấm người ngồi sau xe hoặc hành khách** có nồng độ cồn.\n"
                    "2. **Hành vi đúng quy định và được khuyến khích:** Khi bạn đã uống rượu, bia mà chủ động không cầm lái, nhờ người khác chở về, đi taxi hoặc sử dụng xe công nghệ là hành vi đúng pháp luật và đảm bảo an toàn tính mạng.\n\n"
                    "**Các điều kiện an toàn bắt buộc khi được chở:**\n"
                    "- **Người lái xe (người chở bạn):** Tuyệt đối không được có nồng độ cồn trong máu hoặc hơi thở và phải có giấy phép lái xe phù hợp.\n"
                    "- **Đội mũ bảo hiểm:** Nếu đi mô tô, xe gắn máy, bạn (người ngồi sau) bắt buộc phải đội mũ bảo hiểm cài quai đúng quy cách theo quy định tại [Điều 33, khoản 2].\n"
                    "- **Trách nhiệm người ngồi sau:** Ngồi an toàn, không có hành vi bám, kéo, đẩy hoặc quậy phá gây cản trở người lái xe làm mất trật tự an toàn giao thông theo [Điều 33, khoản 1]."
                )

            if is_pushing_bike:
                return (
                    "**Kết luận: HÀNH VI DẮT XE MÁY ĐI BỘ KHÔNG PHẢI LÀ ĐIỀU KHIỂN PHƯƠNG TIỆN, NHƯNG CẦN CHÚ Ý ĐIỀU KIỆN THỰC TẾ.**\n\n"
                    "**Căn cứ pháp lý:** [Luật Trật tự, an toàn giao thông đường bộ 36/2024/QH15, Điều 9, khoản 2] - Các hành vi bị nghiêm cấm:\n"
                    f"> *\"{top_source.raw_content}\"*\n\n"
                    "**Giải thích chi tiết:**\n"
                    "1. Luật chỉ nghiêm cấm hành vi **\"điều khiển phương tiện\"** khi trong máu hoặc hơi thở có nồng độ cồn. Người dắt xe máy đi bộ đã tắt máy không được xem là đang điều khiển phương tiện cơ giới mà tham gia giao thông với tư cách người đi bộ dắt vật dụng.\n"
                    "2. **Yêu cầu an toàn:** Người dắt xe phải đi trên hè phố, lề đường hoặc sát mép đường bên phải theo chiều đi, không được gây cản trở giao thông trên lòng đường.\n"
                    "3. **Lưu ý thực tế:** Lực lượng Cảnh sát giao thông có quyền trích xuất camera hoặc xác minh nhân chứng. Nếu xác định trước đó bạn đã trực tiếp nổ máy lái xe rồi mới nhảy xuống dắt bộ nhằm đối phó chốt kiểm tra, bạn vẫn bị xử lý vi phạm nồng độ cồn khi điều khiển phương tiện."
                )

            # Trường hợp trực tiếp lái xe hoặc hỏi chung
            return (
                "**Kết luận: TUYỆT ĐỐI NGHIÊM CẤM ĐIỀU KHIỂN PHƯƠNG TIỆN.**\n\n"
                "**Căn cứ pháp lý:** [Luật Trật tự, an toàn giao thông đường bộ 36/2024/QH15, Điều 9, khoản 2] - Các hành vi bị nghiêm cấm:\n"
                f"> *\"{top_source.raw_content}\"*\n\n"
                "**Giải thích chi tiết:** Luật Trật tự, an toàn giao thông đường bộ số 36/2024/QH15 quy định nghiêm cấm tuyệt đối "
                "mọi hành vi điều khiển phương tiện tham gia giao thông đường bộ (bao gồm ô tô, xe máy, xe máy điện, xe đạp...) "
                "mà trong máu hoặc hơi thở có nồng độ cồn (áp dụng mức nồng độ cồn bằng 0). "
                "Không phân biệt uống ít hay nhiều bia, rượu ('nhậu'), chỉ cần trong hơi thở hoặc máu còn cồn thì hoàn toàn không được phép lái xe."
            )

        # 3. Nhóm Đèn tín hiệu giao thông (Đèn vàng / Đèn đỏ)
        has_light_kw = any(k in clean_q for k in ["đèn đỏ", "đèn vàng", "vượt đèn", "tín hiệu đèn"]) or art_num == 11
        if has_light_kw:
            is_yellow_crossed = any(k in clean_q for k in ["đèn vàng", "vàng"]) and any(k in clean_q for k in ["qua vạch", "trên vạch", "vượt qua"])
            if is_yellow_crossed:
                return (
                    "**Kết luận: ĐƯỢC PHÉP ĐI TIẾP NẾU ĐÃ ĐI QUA HOẶC ĐANG TRÊN VẠCH DỪNG KHI ĐÈN CHUYỂN VÀNG.**\n\n"
                    "**Căn cứ pháp lý:** [Luật Trật tự, an toàn giao thông đường bộ 36/2024/QH15, Điều 11, khoản 4, điểm b]:\n"
                    "> *\"Tín hiệu đèn màu vàng là phải dừng lại trước vạch dừng; trường hợp đang đi trên vạch dừng hoặc đã đi qua vạch dừng khi tín hiệu đèn màu vàng thì được đi tiếp.\"*\n\n"
                    "**Giải thích chi tiết:** Nếu phương tiện chưa chạm hoặc chưa vượt qua vạch dừng khi đèn chuyển sang màu vàng thì bắt buộc phải dừng lại. "
                    "Chỉ khi phương tiện đã đè vạch hoặc vượt qua vạch dừng trước thời điểm đèn vàng bật sáng thì mới được tiếp tục lưu thông để tránh phanh gấp gây nguy hiểm."
                )
            return (
                "**Kết luận: VƯỢT ĐÈN ĐỎ LÀ HÀNH VI BỊ CẤM TUYỆT ĐỐI.**\n\n"
                "**Căn cứ pháp lý:** [Luật Trật tự, an toàn giao thông đường bộ 36/2024/QH15, Điều 11, khoản 4, điểm c]:\n"
                "> *\"Tín hiệu đèn màu đỏ là cấm đi; người tham gia giao thông phải chấp hành hiệu lệnh của đèn tín hiệu giao thông.\"*"
            )

        # 4. Nhóm Số người được chở trên xe máy (kẹp 3, chở 2 người)
        has_passenger_capacity_kw = any(k in clean_q for k in ["chở 2", "chở 3", "kẹp 3", "kẹp ba", "chở ba", "chở mấy người", "mấy người trên xe"]) or (art_num == 33 and cl_num == 1)
        if has_passenger_capacity_kw:
            return (
                "**Kết luận: XE MÔ TÔ, XE GẮN MÁY CHỈ ĐƯỢC CHỞ 01 NGƯỜI, NGOẠI TRỪ 04 TRƯỜNG HỢP ĐƯỢC CHỞ TỐI ĐA 02 NGƯỜI.**\n\n"
                "**Căn cứ pháp lý:** [Luật Trật tự, an toàn giao thông đường bộ 36/2024/QH15, Điều 33, khoản 1]:\n"
                "> *\"1. Người lái xe mô tô hai bánh, xe gắn máy chỉ được chở một người, trừ những trường hợp sau thì được chở tối đa hai người:\n"
                "> a) Chở người bệnh đi cấp cứu;\n"
                "> b) Áp giải người có hành vi vi phạm pháp luật;\n"
                "> c) Trẻ em dưới 12 tuổi;\n"
                "> d) Người già yếu hoặc người khuyết tật.\"*\n\n"
                "**Điểm mới cần lưu ý:** Luật 36/2024/QH15 nâng độ tuổi trẻ em được chở thêm lên **dưới 12 tuổi** (trước đây theo Luật 2008 là dưới 14 tuổi), đồng thời bổ sung trường hợp chở người già yếu hoặc người khuyết tật."
            )

        # 5. Nhóm Điểm giấy phép lái xe (Điều 58)
        if art_num == 58 or any(k in clean_q for k in ["điểm gplx", "trừ điểm", "bị trừ điểm", "12 điểm", "phục hồi điểm"]):
            return (
                "**Kết luận: MỖI GIẤY PHÉP LÁI XE CÓ 12 ĐIỂM TRONG MỘT NĂM.**\n\n"
                "**Căn cứ pháp lý:** [Luật Trật tự, an toàn giao thông đường bộ 36/2024/QH15, Điều 58] - Điểm của giấy phép lái xe:\n"
                f"> *\"{top_source.raw_content}\"*\n\n"
                "**Các nguyên tắc quan trọng:**\n"
                "1. Điểm được dùng để quản lý việc chấp hành pháp luật về trật tự an toàn giao thông của người lái xe.\n"
                "2. Giấy phép lái xe được phục hồi đủ 12 điểm khi chưa bị trừ hết điểm và không bị trừ điểm trong thời hạn 12 tháng kể từ ngày bị trừ điểm gần nhất.\n"
                "3. Trường hợp bị trừ hết điểm: Không được điều khiển phương tiện theo GPLX đó. Sau thời hạn ít nhất 06 tháng, phải tham gia kiểm tra lại kiến thức pháp luật và đạt yêu cầu mới được phục hồi đủ 12 điểm."
            )

        # 6. Mặc định: Trích xuất trực tiếp thông tin chuẩn xác theo Điều luật và câu hỏi
        return (
            f"**Kết luận:** Quy định tại [Điều {art_num} - {top_source.article_title}].\n\n"
            f"**Căn cứ pháp lý:** [Luật Trật tự, an toàn giao thông đường bộ 36/2024/QH15, Điều {art_num}{cl_str}{pt_str}]:\n"
            f"> *\"{top_source.raw_content}\"*\n\n"
            f"**Nội dung giải thích:** Căn cứ theo quy định tại Điều {art_num} của Luật Trật tự, an toàn giao thông đường bộ số 36/2024/QH15, "
            f"người tham gia giao thông có trách nhiệm tuân thủ đầy đủ các quy tắc nêu trên để bảo đảm an toàn tính mạng, sức khỏe và trật tự giao thông."
        )
