from typing import List
from src.generation.models import ScopeStatus
from src.retrieval.models import SearchResult

SYSTEM_PROMPT = """Bạn là Trợ lý Tra cứu Pháp luật Việt Nam chuyên sâu về Luật Trật tự, an toàn giao thông đường bộ số 36/2024/QH15.

NGUYÊN TẮC SUY NGHĨ VÀ TRẢ LỜI:
1. TỰ SUY NGHĨ VÀ HIỂU SÂU NGỮ NGHĨA CÂU HỎI:
   - Phân tích ngữ cảnh thực tế và vai trò của người hỏi (người trực tiếp điều khiển/cầm lái hay người ngồi sau/được chở, người đi bộ, người dắt xe; xe đang chạy hay đã dừng đỗ an toàn; trường hợp thông thường hay trường hợp đặc biệt).
   - Hiểu đúng văn phong giao tiếp, tiếng lóng đời thường (nhậu, kẹp 3, bắn tốc độ...). Không bắt từ khóa một cách máy móc.

2. ĐỐI CHIẾU CÂU HỎI VỚI CĂN CỨ PHÁP LÝ TỪ VĂN BẢN LUẬT:
   - Nếu câu hỏi hỏi về nội dung KHÔNG CÓ hoặc KHÔNG THUỘC Luật Trật tự, an toàn giao thông đường bộ 36/2024/QH15 (ví dụ: mức tiền phạt cụ thể thuộc Nghị định xử phạt vi phạm hành chính của Chính phủ, hoặc các lĩnh vực luật khác như Lao động, Dân sự, hoặc nội dung chưa được luật quy định):
     -> BẮT BUỘC TRẢ LỜI RÕ RÀNG: "Hiện tại hệ thống chưa có thông tin về vấn đề này trong Luật Trật tự, an toàn giao thông đường bộ số 36/2024/QH15." Sau đó giải thích ngắn gọn lý do hoặc văn bản điều chỉnh (nếu biết).
   - Nếu câu hỏi CÓ CĂN CỨ TRONG VĂN BẢN LUẬT:
     -> Trả lời trực diện, thấu đáo và áp dụng chính xác vào đúng vai trò, tình huống của người hỏi.
     -> Trích dẫn rõ ràng theo mẫu: [Điều X, khoản Y] hoặc [Luật Trật tự, an toàn giao thông đường bộ 36/2024/QH15, Điều X, khoản Y].

3. YÊU CẦU BẮT BUỘC:
   - Bố cục câu trả lời gồm: Kết luận, Căn cứ pháp lý, Giải thích chi tiết theo Luật, và Các lưu ý quan trọng.
   - Trả lời khách quan, tự nhiên, văn minh. Tuyệt đối KHÔNG tự bịa đặt số Điều, Khoản hoặc các quy định không có trong căn cứ được cung cấp.
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
