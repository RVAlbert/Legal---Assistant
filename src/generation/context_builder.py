from pathlib import Path
from typing import List
from src.generation.models import ScopeStatus
from src.retrieval.models import SearchResult

SKILL_FILE = Path(__file__).resolve().parent / "skills" / "concise_legal_answer.md"


def _load_system_prompt() -> str:
    """Đọc skill hướng dẫn trả lời ngắn gọn, đúng trọng tâm, chuẩn trích dẫn cho AI."""
    base_header = (
        "Bạn là Trợ lý Tra cứu Pháp luật Giao thông Việt Nam, sử dụng 2 văn bản chính thức:\n"
        "1. Luật Trật tự, an toàn giao thông đường bộ số 36/2024/QH15 (quy tắc giao thông, hành vi cấm, GPLX).\n"
        "2. Nghị định số 168/2024/NĐ-CP (mức phạt tiền cụ thể, trừ điểm và phục hồi điểm GPLX).\n\n"
    )
    if SKILL_FILE.exists():
        return base_header + SKILL_FILE.read_text(encoding="utf-8").strip()
    return (
        base_header
        + "Trả lời NGẮN GỌN (2–4 dòng), đúng trọng tâm, không lan man, bắt buộc ghi rõ [Tên văn bản, Điều X, khoản Y, điểm Z]."
    )


SYSTEM_PROMPT = _load_system_prompt()


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
        context_parts.append("=== NGUỒN CĂN CỨ CHÍNH TỪ VĂN BẢN PHÁP LUẬT ===")
        for i, src in enumerate(primary_sources, start=1):
            cl_info = f", Khoản {src.clause_number}" if src.clause_number else ""
            pt_info = f", Điểm {src.point}" if src.point else ""
            doc_tag = "Nghị định 168/2024/NĐ-CP" if "168" in src.law_number else f"Luật {src.law_number}"
            context_parts.append(
                f"[Nguồn {i}: {doc_tag} - Điều {src.article_number}{cl_info}{pt_info} - {src.article_title}]\n"
                f"{src.text}\n"
            )

        # 2. Nguồn tham chiếu bổ sung (nếu có)
        if expansion_sources:
            context_parts.append("\n=== NGUỒN THAM CHIẾU BỔ SUNG ===")
            for j, ref in enumerate(expansion_sources, start=1):
                cl_info = f", Khoản {ref.clause_number}" if ref.clause_number else ""
                pt_info = f", Điểm {ref.point}" if ref.point else ""
                doc_tag = "Nghị định 168/2024/NĐ-CP" if "168" in ref.law_number else f"Luật {ref.law_number}"
                context_parts.append(
                    f"[Nguồn tham chiếu {j}: {doc_tag} - Điều {ref.article_number}{cl_info}{pt_info} - {ref.article_title}]\n"
                    f"{ref.text}\n"
                )

        # 3. Ghi chú về trạng thái dữ liệu (nếu có)
        extra_instruction = ""
        if scope_status == ScopeStatus.INSUFFICIENT_DATA:
            extra_instruction = (
                f"\nLƯU Ý: {scope_note}\n"
                "Nếu nguồn trên không có mức tiền phạt cụ thể cho hành vi được hỏi, hãy nói ngắn gọn rằng hệ thống chưa tìm thấy mức phạt chi tiết này."
            )

        context_text = "\n".join(context_parts)

        user_content = (
            f"CĂN CỨ PHÁP LÝ:\n{context_text}\n"
            f"{extra_instruction}\n"
            f"CÂU HỎI: {query}\n\n"
            "Trả lời NGẮN GỌN, ĐÚNG TRỌNG TÂM (tiết kiệm token), ghi rõ văn bản + Điều, khoản, điểm."
        )

        return [
            {"role": "system", "content": _load_system_prompt()},
            {"role": "user", "content": user_content},
        ]
