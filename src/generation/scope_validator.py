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

    # Danh sách từ khóa hỏi mức tiền phạt cụ thể
    FINE_KEYWORDS = [
        "phạt bao nhiêu tiền", "phạt bao nhiêu", "tiền phạt", "mức phạt tiền",
        "mức phạt bao nhiêu", "bị phạt mấy triệu", "phạt mấy trăm", "phạt bao tiền",
        "mức phạt cụ thể", "nghị định 100", "nghị định 123", "nghị định 168",
    ]

    def assess_pre_retrieval(self, query: str) -> Optional[ScopeAssessment]:
        """Kiểm tra nhanh trước khi tìm kiếm (từ khóa cấm, rỗng hoặc quá ngắn)."""
        clean_q = query.strip().lower()

        if not clean_q or len(clean_q) < 3:
            return ScopeAssessment(
                status=ScopeStatus.OUT_OF_SCOPE,
                reason="Câu hỏi rỗng hoặc quá ngắn để tra cứu.",
            )

        # Kiểm tra từ khóa ngoài phạm vi
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

        # Kiểm tra nếu hỏi mức phạt tiền
        for kw in self.FINE_KEYWORDS:
            if kw in clean_q:
                return ScopeAssessment(
                    status=ScopeStatus.INSUFFICIENT_DATA,
                    reason=(
                        "Luật Trật tự, an toàn giao thông đường bộ số 36/2024/QH15 quy định về quy tắc và hành vi, "
                        "nhưng mức tiền phạt cụ thể được quy định tại Nghị định của Chính phủ về xử phạt vi phạm hành chính "
                        "(văn bản này chưa có trong dữ liệu hiện tại)."
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
