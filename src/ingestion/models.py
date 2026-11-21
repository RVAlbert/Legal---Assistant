from typing import Any, List, Optional
from pydantic import BaseModel, Field


class PointData(BaseModel):
    """Thông tin Điểm (a, b, c...)."""
    point: str
    text: str


class ClauseData(BaseModel):
    """Thông tin Khoản (1, 2, 3...)."""
    clause_number: Optional[int] = None
    text: str
    points: List[PointData] = Field(default_factory=list)


class ArticleData(BaseModel):
    """Thông tin Điều."""
    article_number: int
    article_title: str
    text: str = ""
    clauses: List[ClauseData] = Field(default_factory=list)


class ChapterData(BaseModel):
    """Thông tin Chương."""
    chapter_number: int
    chapter_title: str
    articles: List[ArticleData] = Field(default_factory=list)


class LawDocument(BaseModel):
    """Mô hình dữ liệu toàn bộ văn bản luật."""
    document_id: str = "luat_trat_tu_an_toan_giao_thong_36_2024"
    law_name: str = "Luật Trật tự, an toàn giao thông đường bộ"
    law_number: str = "36/2024/QH15"
    issue_date: str = "27/06/2024"
    effective_date: str = "01/01/2025"
    chapters: List[ChapterData] = Field(default_factory=list)


class LawChunk(BaseModel):
    """Mô hình đơn vị chunk tìm kiếm theo yêu cầu FR-02."""
    id: str
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
