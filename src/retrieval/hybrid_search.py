from typing import Dict, List, Optional
from src.common.config import get_settings
from src.common.logger import get_logger
from src.retrieval.bm25_search import BM25SearchEngine
from src.retrieval.models import SearchResult
from src.retrieval.query_expander import QueryExpander
from src.retrieval.vector_search import VectorSearchEngine

logger = get_logger("hybrid_search")


class HybridSearchEngine:
    """Bộ tìm kiếm lai Hybrid Search kết hợp BM25 và Vector Search bằng Reciprocal Rank Fusion (RRF)."""

    def __init__(
        self,
        bm25_engine: BM25SearchEngine,
        vector_engine: VectorSearchEngine,
        rrf_k: int = 60,
        bm25_weight: float = 1.0,
        semantic_weight: float = 1.0,
    ):
        self.bm25_engine = bm25_engine
        self.vector_engine = vector_engine
        self.rrf_k = rrf_k
        self.bm25_weight = bm25_weight
        self.semantic_weight = semantic_weight

    def search(
        self,
        query: str,
        top_k: int = 8,
        candidate_k: int = 20,
    ) -> List[SearchResult]:
        """Thực hiện tìm kiếm song song BM25 và Semantic sau khi chuẩn hóa/mở rộng ngữ nghĩa đời thường."""
        # Chuẩn hóa và mở rộng từ ngữ đời thường (nhậu, khôn, kẹp 3, bằng lái...) sang thuật ngữ luật
        expanded_query = QueryExpander.expand(query)
        if expanded_query != query:
            logger.info(f"Query được mở rộng: \"{query}\" -> \"{expanded_query}\"")

        # 1. Chạy tìm kiếm từ khóa BM25
        bm25_results = self.bm25_engine.search(expanded_query, top_k=candidate_k)

        # 2. Chạy tìm kiếm ngữ nghĩa Semantic
        semantic_results = self.vector_engine.search(expanded_query, top_k=candidate_k)

        # 3. Tính điểm RRF Fusion
        # RRF_score(d) = sum( weight / (k + rank_i(d)) )
        rrf_scores: Dict[str, float] = {}
        merged_items: Dict[str, SearchResult] = {}

        # Xử lý kết quả BM25 theo thứ hạng thực tế trong danh sách trả về
        for rank, item in enumerate(bm25_results, start=1):
            cid = item.chunk_id
            rrf_score = self.bm25_weight / (self.rrf_k + rank)
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + rrf_score
            merged_items[cid] = item

        # Xử lý kết quả Semantic theo thứ hạng thực tế trong danh sách trả về
        for rank, item in enumerate(semantic_results, start=1):
            cid = item.chunk_id
            rrf_score = self.semantic_weight / (self.rrf_k + rank)
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + rrf_score
            if cid not in merged_items:
                merged_items[cid] = item

        # 4. Sắp xếp danh sách hợp nhất theo điểm RRF giảm dần
        sorted_chunk_ids = sorted(
            rrf_scores.keys(),
            key=lambda cid: rrf_scores[cid],
            reverse=True,
        )

        final_results: List[SearchResult] = []
        for rank, cid in enumerate(sorted_chunk_ids[:top_k], start=1):
            base_item = merged_items[cid]
            final_item = SearchResult(
                chunk_id=base_item.chunk_id,
                score=round(rrf_scores[cid], 5),
                rank=rank,
                document_id=base_item.document_id,
                law_number=base_item.law_number,
                law_name=base_item.law_name,
                chapter_number=base_item.chapter_number,
                chapter_title=base_item.chapter_title,
                article_number=base_item.article_number,
                article_title=base_item.article_title,
                clause_number=base_item.clause_number,
                point=base_item.point,
                text=base_item.text,
                raw_content=base_item.raw_content,
                references=base_item.references,
                source_type="hybrid",
            )
            final_results.append(final_item)

        return final_results
