from typing import List, Optional
from pydantic import BaseModel, Field
from src.generation.models import Citation, ScopeStatus
from src.retrieval.models import SearchResult


class HealthResponse(BaseModel):
    """Phản hồi kiểm tra trạng thái hệ thống."""
    status: str = "ok"
    app_name: str = "VN Legal RAG Assistant"
    version: str = "0.1.0"
    llm_model: str
    embedding_model: str
    total_indexed_chunks: int = 500


class DocumentInfo(BaseModel):
    """Thông tin văn bản luật được hỗ trợ."""
    document_id: str
    law_name: str
    law_number: str
    issue_date: str
    effective_date: str
    total_chapters: int
    total_articles: int
    scope_description: str


class SearchRequest(BaseModel):
    """Yêu cầu tìm kiếm nguồn luật."""
    query: str = Field(..., min_length=1, description="Câu hỏi hoặc từ khóa tra cứu")
    top_k: int = Field(default=5, ge=1, le=20, description="Số lượng kết quả cần lấy")


class SearchResponse(BaseModel):
    """Phản hồi tìm kiếm."""
    query: str
    total_results: int
    results: List[SearchResult]


class ChatRequest(BaseModel):
    """Yêu cầu hỏi đáp trợ lý pháp luật."""
    query: str = Field(..., min_length=1, description="Câu hỏi của người dùng")
    top_k: int = Field(default=5, ge=1, le=10, description="Số lượng chunk ngữ cảnh")


class ChatResponse(BaseModel):
    """Phản hồi hỏi đáp trợ lý pháp luật."""
    query: str
    scope_status: ScopeStatus
    answer: str
    citations: List[Citation]
    sources: List[SearchResult]
    expansion_sources: List[SearchResult]
    warnings: List[str]
    latency_ms: float
