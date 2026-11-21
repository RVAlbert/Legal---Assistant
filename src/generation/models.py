from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from src.retrieval.models import SearchResult


class ScopeStatus(str, Enum):
    """Trạng thái phạm vi của câu hỏi."""
    ANSWERED = "answered"                     # Đủ dữ liệu để trả lời từ Luật 36/2024
    INSUFFICIENT_DATA = "insufficient_data"   # Đúng lĩnh vực nhưng thiếu văn bản (ví dụ mức tiền phạt)
    OUT_OF_SCOPE = "out_of_scope"             # Ngoài phạm vi văn bản / ngoài lĩnh vực pháp luật


class ScopeAssessment(BaseModel):
    """Kết quả đánh giá phạm vi câu hỏi."""
    status: ScopeStatus
    reason: str
    missing_scope: Optional[str] = None


class Citation(BaseModel):
    """Thông tin trích dẫn pháp lý."""
    law_name: str = "Luật Trật tự, an toàn giao thông đường bộ"
    law_number: str = "36/2024/QH15"
    article_number: int
    clause_number: Optional[int] = None
    point: Optional[str] = None
    raw_citation: str
    is_valid: bool = True


class GenerationResponse(BaseModel):
    """Kết quả trả lời hoàn chỉnh của hệ thống."""
    query: str
    scope_status: ScopeStatus
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    sources: List[SearchResult] = Field(default_factory=list)
    expansion_sources: List[SearchResult] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    latency_ms: float = 0.0
