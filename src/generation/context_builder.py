from typing import List
from src.generation.models import ScopeStatus
from src.retrieval.models import SearchResult

SYSTEM_PROMPT = """Bạn là Trợ lý Tra cứu Luật Trật tự, an toàn giao thông đường bộ số 36/2024/QH15.

PHONG CÁCH TRẢ LỜI (BẮT BUỘC):
- **NGẮN GỌN, ĐÚNG TRỌNG TÂM, KHÔNG VÒNG VO** (tối đa khoảng 3–5 câu hoặc 2–4 gạch đầu dòng ngắn).
- **Nói thẳng kết luận + Điều mấy, khoản mấy ngay lập tức** theo định dạng `[Điều X, khoản Y]`.

QUY TẮC XỬ LÝ TÌNH HUỐNG:
1. **Hiểu đúng ngữ cảnh người dùng:** Phân biệt rõ vai trò (người lái xe vs người ngồi sau/được chở, đang chạy vs đã dừng xe...), hiểu văn phong đời thường (nhậu, kẹp 3...). Không bắt từ khóa máy móc.
2. **Câu hỏi có trong Luật 36/2024/QH15:**
   - **Kết luận:** Trả lời thẳng (Được / Không được / Quy định chính) kèm `[Điều X, khoản Y]`.
   - **Giải thích ngắn:** 1–2 ý cốt lõi nhất (hoặc lưu ý bắt buộc nếu có).
3. **Câu hỏi hỏi mức tiền phạt hoặc nội dung KHÔNG có trong Luật 36/2024/QH15:**
   - Nói thẳng ngay dòng đầu: *"Hiện tại hệ thống chưa có thông tin này trong Luật Trật tự, an toàn giao thông đường bộ 36/2024/QH15."*
   - Giải thích 1 câu ngắn (ví dụ: mức tiền phạt cụ thể thuộc Nghị định của Chính phủ; kèm 1 dòng hành vi cấm liên quan `[Điều X, khoản Y]` nếu có).
4. **Giao tiếp xã hội** (chào hỏi, hỏi thăm sức khỏe, lối sống): Trả lời thân thiện, ngắn gọn 1–2 câu.
5. **Câu hỏi lạc đề, ghẹo chọc, châm biếm, không liên quan:** Trả lời đúng câu: *"Hiện tại mình chưa có kết quả bạn yêu cầu, xin thử lại."*
6. Tuyệt đối không bịa đặt số Điều, Khoản hay mức tiền phạt không có trong nguồn.
"""


class ContextBuilder:
    """Bộ lắp ráp Prompt và Ngữ cảnh đưa vào LLM (Bước 13)."""

    def build_prompt(
        self,
        query: str,
        primary_sources: List[SearchResult],
        expansion_sources: List[SearchResult],
        scope_status: ScopeStatus,
        scope_note: str = "",
    ) -> List[dict]:
        """Tạo messages format chuẩn OpenAI chat completions."""
        context_parts = []

        # 1. Nguồn chính
        context_parts.append("=== NGUỒN CĂN CỨ CHÍNH TỪ VĂN BẢN LUẬT ===")
        for i, src in enumerate(primary_sources, start=1):
            cl_info = f", Khoản {src.clause_number}" if src.clause_number else ""
            pt_info = f", Điểm {src.point}" if src.point else ""
            context_parts.append(
                f"[Nguồn {i}: Điều {src.article_number}{cl_info}{pt_info} - {src.article_title}]\n"
                f"{src.text}\n"
            )

        # 2. Nguồn tham chiếu bổ sung (nếu có)
        if expansion_sources:
            context_parts.append("\n=== NGUỒN THAM CHIẾU DẪN CHIẾU BỔ SUNG ===")
            for j, ref in enumerate(expansion_sources, start=1):
                cl_info = f", Khoản {ref.clause_number}" if ref.clause_number else ""
                pt_info = f", Điểm {ref.point}" if ref.point else ""
                context_parts.append(
                    f"[Nguồn tham chiếu {j}: Điều {ref.article_number}{cl_info}{pt_info} - {ref.article_title}]\n"
                    f"{ref.text}\n"
                )

        # 3. Ghi chú về trạng thái dữ liệu (nếu có)
        extra_instruction = ""
        if scope_status == ScopeStatus.INSUFFICIENT_DATA:
            extra_instruction = (
                f"\nLƯU Ý QUAN TRỌNG: {scope_note}\n"
                "Người dùng đang hỏi về MỨC TIỀN PHẠT CỤ THỂ. "
                "YÊU CẦU BẮT BUỘC:\n"
                "1. Kết luận PHẢI nêu rõ ngay đầu câu: Hiện tại hệ thống CHƯA CÓ thông tin về mức tiền phạt cụ thể này, "
                "vì mức tiền phạt thuộc Nghị định của Chính phủ về xử phạt vi phạm hành chính (chưa có trong dữ liệu).\n"
                "2. Sau đó mới trích dẫn quy tắc hoặc hành vi bị nghiêm cấm tương ứng có trong Luật 36/2024/QH15.\n"
                "3. Tuyệt đối không tự suy đoán hoặc bịa ra con số tiền phạt."
            )

        context_text = "\n".join(context_parts)

        user_content = (
            f"CĂN CỨ PHÁP LÝ:\n{context_text}\n"
            f"{extra_instruction}\n"
            f"CÂU HỎI CỦA NGƯỜI DÙNG: {query}\n\n"
            "Hãy trả lời câu hỏi dựa trên Căn cứ pháp lý ở trên theo đúng các quy tắc bắt buộc."
        )

        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]
