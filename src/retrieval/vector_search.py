import os
from pathlib import Path
from typing import List, Optional
import torch
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)
from sentence_transformers import SentenceTransformer

from src.common.config import get_settings
from src.common.logger import get_logger
from src.ingestion.models import LawChunk
from src.retrieval.models import SearchResult

logger = get_logger("vector_search")


class VectorSearchEngine:
    """Bộ tìm kiếm ngữ nghĩa (Semantic Search) sử dụng BAAI/bge-m3 và Qdrant."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        qdrant_client: Optional[QdrantClient] = None,
    ):
        settings = get_settings()
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.collection_name = settings.QDRANT_COLLECTION

        # Xác định thiết bị tính toán: cuda nếu có, ngược lại cpu
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Khởi tạo Embedding Model: {self.model_name} trên {self.device.upper()}")
        self.embedder = SentenceTransformer(self.model_name, device=self.device)

        # Khởi tạo Qdrant Client (ưu tiên Local on-disk persistent path)
        if qdrant_client:
            self.client = qdrant_client
        elif settings.QDRANT_URL:
            logger.info(f"Kết nối Qdrant qua URL: {settings.QDRANT_URL}")
            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY or None,
            )
        else:
            qdrant_path = Path(settings.QDRANT_PATH)
            qdrant_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Sử dụng Qdrant storage cục bộ tại: {qdrant_path}")
            self.client = QdrantClient(path=str(qdrant_path))

    def create_collection(self, recreate: bool = False):
        """Tạo collection cho Qdrant với vector size tương ứng (bge-m3 = 1024)."""
        vector_size = self.embedder.get_embedding_dimension()

        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name in collections:
            if recreate:
                logger.info(f"Xóa và tạo mới collection: {self.collection_name}")
                self.client.delete_collection(collection_name=self.collection_name)
            else:
                logger.info(f"Collection {self.collection_name} đã tồn tại.")
                return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        logger.info(f"Đã tạo collection {self.collection_name} với vector size {vector_size}")

    def index_chunks(self, chunks: List[LawChunk], batch_size: int = 32):
        """Tạo vector embeddings và nạp vào Qdrant."""
        self.create_collection(recreate=True)

        logger.info(f"Bắt đầu encode {len(chunks)} chunks với batch size {batch_size}...")
        texts = [chunk.text for chunk in chunks]
        embeddings = self.embedder.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            normalize_embeddings=True,
        )

        points = []
        for i, (chunk, vector) in enumerate(zip(chunks, embeddings)):
            payload = {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "law_number": chunk.law_number,
                "law_name": chunk.law_name,
                "chapter_number": chunk.chapter_number,
                "chapter_title": chunk.chapter_title,
                "article_number": chunk.article_number,
                "article_title": chunk.article_title,
                "clause_number": chunk.clause_number,
                "point": chunk.point,
                "text": chunk.text,
                "raw_content": chunk.raw_content,
                "references": chunk.references,
            }
            points.append(
                PointStruct(
                    id=i + 1,
                    vector=vector.tolist(),
                    payload=payload,
                )
            )

        # Upload vào Qdrant theo batch
        for i in range(0, len(points), 64):
            batch = points[i : i + 64]
            self.client.upsert(collection_name=self.collection_name, points=batch)

        logger.info(f"Đã nạp thành công {len(points)} vector vào collection {self.collection_name}.")

    def search(
        self,
        query: str,
        top_k: int = 10,
        article_filter: Optional[int] = None,
    ) -> List[SearchResult]:
        """Tìm kiếm vector gần nghĩa nhất với query."""
        query_vector = self.embedder.encode(
            query,
            normalize_embeddings=True,
        ).tolist()

        q_filter = None
        if article_filter is not None:
            q_filter = Filter(
                must=[
                    FieldCondition(
                        key="article_number",
                        match=MatchValue(value=article_filter),
                    )
                ]
            )

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=q_filter,
            limit=top_k,
        )

        results = []
        for rank, pt in enumerate(response.points, start=1):
            p = pt.payload
            results.append(
                SearchResult(
                    chunk_id=p["chunk_id"],
                    score=float(pt.score),
                    rank=rank,
                    document_id=p["document_id"],
                    law_number=p["law_number"],
                    law_name=p["law_name"],
                    chapter_number=p["chapter_number"],
                    chapter_title=p["chapter_title"],
                    article_number=p["article_number"],
                    article_title=p["article_title"],
                    clause_number=p["clause_number"],
                    point=p["point"],
                    text=p["text"],
                    raw_content=p["raw_content"],
                    references=p["references"],
                    source_type="semantic",
                )
            )
        return results
