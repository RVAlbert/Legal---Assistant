from typing import List, Optional
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """Kết quả tìm kiếm cho một chunk luật."""
    chunk_id: str
    score: float = 0.0
    rank: int = 0
    document_id: str = "luat_trat_tu_an_toan_giao_thong_36_2024"
    law_number: str = "36/2024/QH15"
    law_name: str = "Luật Trật tự, an toàn giao thông đường bộ"
    chapter_number: int
    chapter_title: str
    article_number: int
    article_title: str
    clause_number: Optional[int] = None
    point: Optional[str] = None
    text: str
    raw_content: str
    references: List[str] = Field(default_factory=list)
    source_type: str = "hybrid"  # "bm25", "semantic", "hybrid"
