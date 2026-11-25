import re
from typing import Any, List, Optional, Set
from src.common.logger import get_logger
from src.retrieval.models import SearchResult

logger = get_logger("cross_ref_expander")


class CrossReferenceExpander:
    """Bộ mở rộng tham chiếu chéo (Bước 12).

    Khi các chunk hàng đầu dẫn chiếu sang Điều hoặc Khoản khác (ví dụ: 'Điều 58', 'Khoản 2 Điều 10'),
    tự động truy xuất bổ sung tối đa 2 chunk của Điều được dẫn chiếu để LLM có ngữ cảnh hoàn chỉnh.
    """

    def __init__(self, vector_engine: Optional[Any] = None, max_expansions: int = 2):
        self.vector_engine = vector_engine
        self.max_expansions = max_expansions

    def expand(self, primary_results: List[SearchResult]) -> List[SearchResult]:
        if not primary_results or self.vector_engine is None:
            return []

        # Tập hợp các Điều đã có trong nguồn chính
        existing_articles: Set[int] = set(r.article_number for r in primary_results)
        expanded_chunks: List[SearchResult] = []

        for res in primary_results:
            if len(expanded_chunks) >= self.max_expansions:
                break

            for ref in res.references:
                if len(expanded_chunks) >= self.max_expansions:
                    break

                # Trích xuất số Điều từ tham chiếu (ví dụ: 'Điều 58' hoặc 'Khoản 2 Điều 10')
                m_art = re.search(r"Điều\s+(\d+)", ref, re.IGNORECASE)
                if not m_art:
                    continue

                target_article = int(m_art.group(1))

                # Chỉ mở rộng nếu Điều đó chưa có trong danh sách kết quả chính và chưa được mở rộng
                if target_article not in existing_articles and 1 <= target_article <= 89:
                    logger.info(f"Mở rộng tham chiếu từ chunk {res.chunk_id} sang Điều {target_article}")
                    ref_results = self.vector_engine.search(
                        query=f"Điều {target_article}",
                        top_k=1,
                        article_filter=target_article,
                    )
                    if ref_results:
                        ref_chunk = ref_results[0]
                        ref_chunk.source_type = "reference"
                        expanded_chunks.append(ref_chunk)
                        existing_articles.add(target_article)

        return expanded_chunks
