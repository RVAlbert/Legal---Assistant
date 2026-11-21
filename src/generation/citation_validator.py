import re
from typing import List, Set
from src.generation.models import Citation
from src.retrieval.models import SearchResult


class CitationValidator:
    """Bộ kiểm tra tính hợp lệ của trích dẫn (Bước 16).

    Kiểm tra xem các Điều/Khoản xuất hiện trong câu trả lời có thực sự tồn tại
    trong danh sách nguồn (primary + expansion) được cung cấp cho LLM hay không,
    ngăn ngừa tình trạng bịa Điều (hallucination).
    """

    def validate_citations(
        self,
        answer_text: str,
        available_sources: List[SearchResult],
    ) -> tuple[List[Citation], List[str]]:
        citations: List[Citation] = []
        warnings: List[str] = []

        # Tập hợp các Điều có trong các chunk được cung cấp
        valid_articles: Set[int] = set(s.article_number for s in available_sources)

        # Regex tìm các mẫu trích dẫn trong câu trả lời
        # Ví dụ: [Điều 58, khoản 1], [Luật ..., Điều 9, khoản 2], Điều 9
        citation_pattern = re.compile(
            r"\[?(?:Luật[^,]+,\s*)?Điều\s+(\d+)(?:,\s*khoản\s+(\d+))?(?:,\s*điểm\s+([a-zđ]))?\]?",
            re.IGNORECASE,
        )

        found_matches = list(citation_pattern.finditer(answer_text))

        seen_citations = set()
        for m in found_matches:
            art_num = int(m.group(1))
            cl_num = int(m.group(2)) if m.group(2) else None
            pt_char = m.group(3).lower() if m.group(3) else None
            raw_cit = m.group(0).strip("[]")

            cit_key = (art_num, cl_num, pt_char)
            if cit_key in seen_citations:
                continue
            seen_citations.add(cit_key)

            is_valid = art_num in valid_articles

            if not is_valid:
                warning_msg = (
                    f"Cảnh báo: Trích dẫn Điều {art_num} không nằm trong tài liệu nguồn được truy xuất (nguy cơ ảo giác)."
                )
                warnings.append(warning_msg)

            citations.append(
                Citation(
                    article_number=art_num,
                    clause_number=cl_num,
                    point=pt_char,
                    raw_citation=raw_cit,
                    is_valid=is_valid,
                )
            )

        # Nếu không có trích dẫn nào trong câu trả lời
        if not citations and available_sources:
            warnings.append("Cảnh báo: Câu trả lời chưa có trích dẫn Điều/Khoản cụ thể.")

        return citations, warnings
