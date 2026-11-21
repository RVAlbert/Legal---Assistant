import pickle
import re
from pathlib import Path
from typing import Dict, List, Optional
from rank_bm25 import BM25Plus

from src.common.logger import get_logger
from src.ingestion.models import LawChunk
from src.retrieval.models import SearchResult

logger = get_logger("bm25_search")


def tokenize_vietnamese(text: str) -> List[str]:
    """Tokenize tiếng Việt giữ lại toàn bộ chữ có dấu, số Điều, hạng bằng lái (A1, B1...), số thập phân."""
    text = text.lower().strip()
    # Tách từ tiếng Việt, số, mã điều luật (ví dụ: điều, khoản, a1, b2, 36/2024/qh15)
    tokens = re.findall(r"[\w]+(?:/[\w]+)*", text)
    return tokens


class BM25SearchEngine:
    """Bộ tìm kiếm từ khóa BM25 cho các văn bản pháp luật."""

    def __init__(self):
        self.bm25: Optional[BM25Plus] = None
        self.chunks: List[LawChunk] = []
        self.corpus_tokens: List[List[str]] = []

    def build_index(self, chunks: List[LawChunk]):
        """Xây dựng chỉ mục BM25 từ danh sách chunk."""
        self.chunks = chunks
        self.corpus_tokens = [tokenize_vietnamese(chunk.text) for chunk in chunks]
        self.bm25 = BM25Plus(self.corpus_tokens)
        logger.info(f"Đã xây dựng BM25Plus index cho {len(chunks)} chunks.")

    def save(self, file_path: Path):
        """Lưu chỉ mục BM25 xuống đĩa."""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as f:
            pickle.dump(
                {
                    "chunks": [c.model_dump() for c in self.chunks],
                    "corpus_tokens": self.corpus_tokens,
                },
                f,
            )
        logger.info(f"Đã lưu BM25 index vào {file_path}")

    def load(self, file_path: Path):
        """Đọc chỉ mục BM25 từ đĩa."""
        if not file_path.exists():
            raise FileNotFoundError(f"Không tìm thấy file index BM25: {file_path}")

        with open(file_path, "rb") as f:
            data = pickle.load(f)
            self.chunks = [LawChunk(**c) for c in data["chunks"]]
            self.corpus_tokens = data["corpus_tokens"]
            self.bm25 = BM25Plus(self.corpus_tokens)
        logger.info(f"Đã load BM25 index ({len(self.chunks)} chunks) từ {file_path}")

    def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Tìm kiếm các chunk liên quan nhất theo BM25."""
        if not self.bm25 or not self.chunks:
            raise RuntimeError("BM25 index chưa được khởi tạo hoặc load.")

        query_tokens = tokenize_vietnamese(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)

        # Lấy top_k điểm cao nhất
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for rank, idx in enumerate(ranked_indices, start=1):
            score = float(scores[idx])
            if score <= 0.0:
                continue
            chunk = self.chunks[idx]
            results.append(
                SearchResult(
                    chunk_id=chunk.id,
                    score=score,
                    rank=rank,
                    document_id=chunk.document_id,
                    law_number=chunk.law_number,
                    law_name=chunk.law_name,
                    chapter_number=chunk.chapter_number,
                    chapter_title=chunk.chapter_title,
                    article_number=chunk.article_number,
                    article_title=chunk.article_title,
                    clause_number=chunk.clause_number,
                    point=chunk.point,
                    text=chunk.text,
                    raw_content=chunk.raw_content,
                    references=chunk.references,
                    source_type="bm25",
                )
            )
        return results
