"""Script tạo toàn bộ chỉ mục BM25 và Vector Qdrant từ data/processed/chunks.jsonl."""

import json
import sys
import time
from pathlib import Path

# Thêm thư mục gốc vào sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.common.config import get_settings
from src.common.logger import setup_logger
from src.ingestion.models import LawChunk
from src.retrieval.bm25_search import BM25SearchEngine
from src.retrieval.hybrid_search import HybridSearchEngine
from src.retrieval.vector_search import VectorSearchEngine

logger = setup_logger("build_indexes")


def main():
    settings = get_settings()
    chunks_file = settings.PROCESSED_DIR / "chunks.jsonl"
    bm25_index_file = settings.INDEXES_DIR / "bm25_index.pkl"

    if not chunks_file.exists():
        logger.error(f"File {chunks_file} không tồn tại. Hãy chạy ingestion trước.")
        sys.exit(1)

    # 1. Đọc danh sách chunks
    logger.info(f"Đọc dữ liệu từ {chunks_file}...")
    chunks = []
    with open(chunks_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(LawChunk(**json.loads(line)))
    logger.info(f"Đã load {len(chunks)} chunks.")

    # 2. Xây dựng và lưu BM25 Index
    t0 = time.time()
    logger.info("Xây dựng chỉ mục BM25...")
    bm25_engine = BM25SearchEngine()
    bm25_engine.build_index(chunks)
    bm25_engine.save(bm25_index_file)
    logger.info(f"BM25 index hoàn tất trong {time.time() - t0:.2f}s")

    # 3. Xây dựng và lưu Vector Index vào Qdrant
    t1 = time.time()
    logger.info("Xây dựng chỉ mục Vector với BAAI/bge-m3 và Qdrant...")
    vector_engine = VectorSearchEngine()
    vector_engine.index_chunks(chunks)
    logger.info(f"Vector index hoàn tất trong {time.time() - t1:.2f}s")

    # 4. Kiểm tra tìm kiếm Hybrid Search với các câu hỏi mẫu
    logger.info("Khởi tạo Hybrid Search Engine (RRF)...")
    hybrid_engine = HybridSearchEngine(bm25_engine=bm25_engine, vector_engine=vector_engine)

    test_queries = [
        ("TC-01: Tình huống đời thường", "Uống ít bia mà trong hơi thở vẫn có cồn thì có được lái xe không?", 9),
        ("TC-04: Chuyên môn GPLX", "Bằng lái hạng A1 được điều khiển loại xe nào?", 57),
        ("TC-05: Cơ chế mới (Số Điều)", "Điều 58 quy định gì về điểm giấy phép lái xe?", 58),
    ]

    print("\n" + "=" * 70)
    print("KẾT QUẢ KIỂM TRA TÌM KIẾM HYBRID SEARCH (BM25 + BGE-M3 + RRF)")
    print("=" * 70)

    for label, query, expected_art in test_queries:
        t_start = time.time()
        results = hybrid_engine.search(query, top_k=5)
        latency = (time.time() - t_start) * 1000

        print(f"\n[Truy vấn] ({label})")
        print(f"Câu hỏi: \"{query}\"")
        print(f"Điều kỳ vọng: Điều {expected_art} | Độ trễ tìm kiếm: {latency:.1f}ms")
        print("Top kết quả trả về:")

        found_expected = False
        for r in results:
            is_match = (r.article_number == expected_art)
            if is_match:
                found_expected = True
            mark = "=> [CHÍNH XÁC]" if is_match else "   "
            pt_info = f" (Điểm {r.point})" if r.point else ""
            cl_info = f", Khoản {r.clause_number}" if r.clause_number else ""
            print(f" {mark} #{r.rank} [Điều {r.article_number}{cl_info}{pt_info}] - Điểm RRF: {r.score:.5f}")
            print(f"       Tiêu đề: {r.article_title}")
            print(f"       Nội dung rút gọn: {r.raw_content[:90]}...")

        status = "ĐẠT" if found_expected else "CHƯA ĐẠT"
        print(f"-> Đánh giá: {status} (Tìm thấy Điều {expected_art} trong Top 5: {found_expected})")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
