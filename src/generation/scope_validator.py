import re
from typing import List, Optional
from src.generation.models import ScopeAssessment, ScopeStatus
from src.retrieval.models import SearchResult


class ScopeValidator:
    """Bộ phân loại phạm vi câu hỏi (Bước 11).

    Phân chia câu hỏi thành 3 trạng thái nghiệp vụ:
    1. OUT_OF_SCOPE: Câu hỏi ngoài phạm vi (Luật Lao động, Thuế, Hình sự, lập trình, câu vô nghĩa).
    2. INSUFFICIENT_DATA: Câu hỏi đúng lĩnh vực nhưng hỏi mức tiền phạt cụ thể (thuộc Nghị định xử phạt).
    3. ANSWERED: Câu hỏi có căn cứ trong Luật Trật tự, an toàn giao thông đường bộ số 36/2024/QH15.
    """

    # Danh sách từ khóa ngoài phạm vi giao thông
    OUT_OF_SCOPE_KEYWORDS = [
        "luật lao động", "thử việc", "hợp đồng lao động", "nghỉ phép năm",
        "thuế thu nhập", "thuế tncn", "luật thuế", "quyết toán thuế",
        "bộ luật dân sự", "luật dân sự", "thừa kế", "ly hôn", "kết hôn",
        "bộ luật hình sự", "luật hình sự", "tội phạm",
        "lập trình", "python", "javascript", "viết code", "viết thơ", "bài thơ", "thơ ", "thơ ngắn",
        "dịch tiếng anh", "thời tiết hôm nay", "kể chuyện", "viết văn",
    ]

    # Nhóm câu giao tiếp xã hội, chào hỏi, thăm hỏi lối sống
    SOCIAL_GREETING_PATTERNS = re.compile(
        r"^(chào( bạn| bot| em| anh| ad)?|xin chào|hello|hi|helo|alo|hế lô)\b|"
        r"\b(bạn khỏe không|bạn khỏe ko|khoe khong|khoe ko|hôm nay thế nào)\b|"
        r"\b(bạn tên gì|bạn là ai|bạn là gì|giới thiệu về bạn)\b|"
        r"\b(cảm ơn|cảm ơn bạn|thanks|thank you|tạm biệt|bye|bye bye)\b",
        re.IGNORECASE,
    )

    # Nhóm câu hỏi lạc đề, ghẹo chọc, châm biếm, vô nghĩa
    TEASING_OFF_TOPIC_PATTERNS = re.compile(
        r"\b(bạn hiểu ý (mình|tôi|ta)( nói)? (ko|không|hông|chưa)?)\b|"
        r"\b(bạn (có )?hiểu (không|ko|hông|chưa|được không))\b|"
        r"^(hiểu (không|ko|hông|chưa)|có hiểu không)\??$|"
        r"\b(bạn (ngốc|ngu|dở|khùng|điên|thông minh))\b|"
        r"\b(kể chuyện|kể chuyện cười|hát|hát một bài|chuyện tình yêu|tâm sự đi)\b|"
        r"\b(ghẹo|chọc tí|đùa tí|nói linh tinh)\b",
        re.IGNORECASE,
    )

    # Danh sách từ khóa hỏi mức tiền phạt cụ thể
    FINE_KEYWORDS = [
        "phạt bao nhiêu tiền", "phạt bao nhiêu", "tiền phạt", "mức phạt tiền",
        "mức phạt bao nhiêu", "bị phạt mấy triệu", "phạt mấy trăm", "phạt bao tiền",
        "mức phạt cụ thể", "nghị định 100", "nghị định 123", "nghị định 168",
        # Biến thể tiếng lóng / viết tắt
        "phạt bao nhiu", "bao nhiu tiền", "bị phạt bao nhiu", "bị phạt bao nhiêu",
        "phạt mấy tiền", "phạt mấy đồng", "bị phạt bao tiền", "phạt mấy củ",
        "phạt bao nhiêu triệu", "mức tiền phạt", "tiền bị phạt", "phạt bn",
        "bao nhiêu củ", "mấy củ", "mấy triệu",
    ]

    # Pattern regex kiểm tra ý định hỏi mức tiền phạt
    FINE_PATTERN = re.compile(
        r"(phạt|tước bằng|giam xe).*?(bao nhiêu|bao nhiu|bn|mấy|tiền|triệu|tr|củ)|"
        r"(bao nhiêu|bao nhiu|bn|mấy).*?(tiền|triệu|tr|củ)|"
        r"mức phạt|tiền phạt",
        re.IGNORECASE,
    )

    def assess_pre_retrieval(self, query: str) -> Optional[ScopeAssessment]:
        """Kiểm tra nhanh trước khi tìm kiếm (giao tiếp xã hội, ghẹo chọc lạc đề, ngoài phạm vi)."""
        clean_q = query.strip().lower()

        if not clean_q or len(clean_q) < 3:
            return ScopeAssessment(
                status=ScopeStatus.OUT_OF_SCOPE,
                reason="Câu hỏi rỗng hoặc quá ngắn để tra cứu.",
            )

        # 1. Đường đi 1: Giao tiếp xã hội / Chào hỏi thân thiện về đời sống
        if self.SOCIAL_GREETING_PATTERNS.search(clean_q):
            return ScopeAssessment(
                status=ScopeStatus.ANSWERED,
                reason=(
                    "Chào bạn! Mình là Trợ lý AI hỗ trợ tra cứu **Luật Trật tự, an toàn giao thông đường bộ số 36/2024/QH15**. "
                    "Mình rất khỏe và luôn sẵn sàng hỗ trợ bạn! "
                    "Hôm nay bạn có câu hỏi hay tình huống giao thông nào cần mình giải đáp không?"
                ),
            )

        # 2. Đường đi 2: Câu hỏi lạc đề, ghẹo chọc, châm biếm
        if self.TEASING_OFF_TOPIC_PATTERNS.search(clean_q):
            return ScopeAssessment(
                status=ScopeStatus.OUT_OF_SCOPE,
                reason="Hiện tại mình chưa có kết quả bạn yêu cầu, xin thử lại. Bạn vui lòng đặt câu hỏi liên quan đến Luật Trật tự, an toàn giao thông đường bộ số 36/2024/QH15 để mình hỗ trợ nhé!",
            )

        # 3. Kiểm tra từ khóa ngoài phạm vi giao thông
        for kw in self.OUT_OF_SCOPE_KEYWORDS:
            if kw in clean_q:
                return ScopeAssessment(
                    status=ScopeStatus.OUT_OF_SCOPE,
                    reason=f"Tài liệu hiện tại chỉ hỗ trợ tra cứu Luật Trật tự, an toàn giao thông đường bộ số 36/2024/QH15 và chưa có dữ liệu về lĩnh vực bạn đang hỏi ({kw}).",
                    missing_scope=kw,
                )

        return None

    def assess_post_retrieval(
        self,
        query: str,
        retrieval_results: List[SearchResult],
    ) -> ScopeAssessment:
        """Kiểm tra sau khi tìm kiếm kết hợp kết quả truy xuất."""
        clean_q = query.strip().lower()

        # Kiểm tra nếu hỏi mức phạt tiền:
        # Nếu đã truy xuất được dữ liệu từ Nghị định 168/2024/NĐ-CP -> ANSWERED!
        # Chỉ báo INSUFFICIENT_DATA nếu hệ thống chưa có kết quả từ Nghị định xử phạt.
        is_fine_query = any(kw in clean_q for kw in self.FINE_KEYWORDS) or bool(self.FINE_PATTERN.search(clean_q))
        if is_fine_query:
            has_decree_source = any("168" in (r.law_number or "") for r in retrieval_results)
            if not has_decree_source:
                return ScopeAssessment(
                    status=ScopeStatus.INSUFFICIENT_DATA,
                    reason=(
                        "Chưa tìm thấy mức tiền phạt cụ thể tương ứng trong Nghị định xử phạt vi phạm hành chính."
                    ),
                    missing_scope="Nghị định xử phạt vi phạm hành chính",
                )

        # Nếu không có kết quả tìm kiếm nào hoặc điểm RRF quá thấp
        if not retrieval_results or retrieval_results[0].score < 0.015:
            return ScopeAssessment(
                status=ScopeStatus.OUT_OF_SCOPE,
                reason="Không tìm thấy điều khoản luật nào đủ liên quan trong Luật Trật tự, an toàn giao thông đường bộ 36/2024/QH15.",
            )

        return ScopeAssessment(
            status=ScopeStatus.ANSWERED,
            reason="Tìm thấy điều khoản phù hợp trong văn bản luật đã nạp.",
        )
