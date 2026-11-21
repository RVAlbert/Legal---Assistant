"""Script chạy toàn bộ quy trình Ingestion: Parse DOCX -> Chunking -> Xuất JSONL."""

import json
import sys
from pathlib import Path

# Thêm thư mục gốc vào sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.common.config import get_settings
from src.common.logger import setup_logger
from src.ingestion.chunker import StructureAwareChunker
from src.ingestion.docx_parser import DocxLawParser

logger = setup_logger("run_ingestion")


def run_ingestion():
    settings = get_settings()
    input_file = settings.INPUT_DIR / "luat_giao_thong_2024_clean.docx"
    output_doc_json = settings.PROCESSED_DIR / "law_document.json"
    output_chunks_jsonl = settings.PROCESSED_DIR / "chunks.jsonl"

    settings.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"1. Bắt đầu parse file: {input_file}")
    parser = DocxLawParser(input_file)
    law_doc = parser.parse()

    # Lưu bản cấu trúc văn bản
    with open(output_doc_json, "w", encoding="utf-8") as f:
        json.dump(law_doc.model_dump(), f, ensure_ascii=False, indent=2)
    logger.info(f"Đã lưu cấu trúc văn bản vào: {output_doc_json}")

    # Thực hiện Chunking
    logger.info("2. Bắt đầu chia chunk bằng Structure-Aware Chunking...")
    chunker = StructureAwareChunker(max_article_chars=1200, max_clause_chars=1000)
    chunks = chunker.chunk_document(law_doc)

    logger.info(f"Tổng số chunks tạo ra: {len(chunks)}")

    # Ghi ra file chunks.jsonl
    with open(output_chunks_jsonl, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk.model_dump(), ensure_ascii=False) + "\n")
    logger.info(f"Đã lưu chunks vào: {output_chunks_jsonl}")

    # BƯỚC 6: Kiểm tra dữ liệu sau chunking
    print("\n" + "=" * 60)
    print("BÁO CÁO KIỂM TRA CHUNKING (BƯỚC 6)")
    print("=" * 60)
    print(f"- Tổng số chunks: {len(chunks)}")

    empty_chunks = [c for c in chunks if not c.text.strip()]
    print(f"- Số chunk rỗng: {len(empty_chunks)}")
    assert len(empty_chunks) == 0, "Lỗi: Có chunk rỗng!"

    # Kiểm tra metadata
    missing_meta = [
        c.id for c in chunks
        if not c.law_name or not c.law_number or not c.chapter_title or not c.article_title
    ]
    print(f"- Số chunk thiếu metadata cốt lõi: {len(missing_meta)}")
    assert len(missing_meta) == 0, "Lỗi: Metadata bị thiếu!"

    # Kiểm tra truy ngược về 89 Điều
    covered_articles = set(c.article_number for c in chunks)
    print(f"- Số Điều được bao phủ trong chunks: {len(covered_articles)} / 89")
    missing_articles = [x for x in range(1, 90) if x not in covered_articles]
    print(f"- Các Điều bị thiếu: {missing_articles}")
    assert len(missing_articles) == 0, f"Lỗi: Thiếu Điều trong chunks: {missing_articles}"

    # Thống kê phân loại chunk
    chunk_whole_articles = [c for c in chunks if c.clause_number is None and c.point is None]
    chunk_clauses = [c for c in chunks if c.clause_number is not None and c.point is None]
    chunk_points = [c for c in chunks if c.point is not None]
    chunks_with_refs = [c for c in chunks if c.references]

    print(f"- Số chunk giữ trọn cả Điều: {len(chunk_whole_articles)}")
    print(f"- Số chunk theo Khoản: {len(chunk_clauses)}")
    print(f"- Số chunk theo Điểm: {len(chunk_points)}")
    print(f"- Số chunk có phát hiện tham chiếu chéo: {len(chunks_with_refs)}")

    # Độ dài thống kê
    lens = [len(c.text) for c in chunks]
    print(f"- Độ dài chunk (ký tự): min={min(lens)}, max={max(lens)}, avg={sum(lens)//len(lens)}")
    print("=" * 60 + "\n")

    return chunks


if __name__ == "__main__":
    run_ingestion()
