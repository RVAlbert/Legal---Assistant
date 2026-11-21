from typing import List
from src.generation.models import ScopeStatus
from src.retrieval.models import SearchResult

SYSTEM_PROMPT = """Bạn là Trợ lý Tra cứu Pháp luật Việt Nam, chuyên về Luật Trật tự, an toàn giao thông đường bộ số 36/2024/QH15.

NHIỆM VỤ:
Trả lời câu hỏi của người dùng một cách chính xác, khách quan, dựa TUYỆT ĐỐI vào các CĂN CỨ PHÁP LÝ được cung cấp dưới đây.

QUY TẮC BẮT BUỘC (TUÂN THỦ 100%):
1. CHỈ sử dụng nội dung có trong các đoạn trích dẫn được cung cấp. Tuyệt đối KHÔNG tự suy đoán, KHÔNG bịa đặt số Điều, Khoản, Điểm hoặc các mốc thời gian, quy định không xuất hiện trong nguồn.
2. KHÔNG tự đưa ra mức tiền phạt cụ thể (ví dụ: phạt bao nhiêu triệu đồng) nếu trong căn cứ được cung cấp không có con số đó. Nếu người dùng hỏi mức tiền phạt, hãy giải thích rõ hành vi theo Luật và thông báo rằng mức tiền phạt cụ thể thuộc Nghị định xử phạt vi phạm hành chính của Chính phủ (chưa có trong dữ liệu hiện tại).
3. GẮN TRÍCH DẪN RÕ RÀNG cho từng ý pháp lý theo định dạng:
   [Luật Trật tự, an toàn giao thông đường bộ 36/2024/QH15, Điều X, khoản Y] (hoặc rút gọn: [Điều X, khoản Y]).
4. BỐ CỤC CÂU TRẢ LỜI:
   - **Kết luận:** Trả lời trực diện vào câu hỏi (Được / Không được / Quy định chung).
   - **Nội dung quy định:** Trình bày rõ các điều kiện, ngoại lệ hoặc trường hợp áp dụng kèm trích dẫn.
   - **Căn cứ pháp lý:** Tóm tắt danh sách Điều, Khoản đã sử dụng.
   - **Lưu ý / Giới hạn dữ liệu (nếu có):** Nêu rõ nếu câu hỏi cần văn bản hướng dẫn bổ sung.
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
                f"\nLƯU Ý NGHIỆP VỤ ĐẶC BIỆT: {scope_note}\n"
                "Người dùng đang hỏi về mức tiền phạt hoặc thông tin ngoài luật này. "
                "Hãy giải thích quy định/hành vi có trong luật được trích dẫn, và nêu rõ hệ thống chưa có văn bản quy định mức tiền phạt cụ thể."
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
