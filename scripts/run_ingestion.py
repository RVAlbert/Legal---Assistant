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
from src.ingestion.text_parser import TextLawParser

logger = setup_logger("run_ingestion")


def run_ingestion():
    settings = get_settings()
    input_file = settings.INPUT_DIR / "luat_giao_thong_2024_clean.docx"
    nd168_file = settings.PROCESSED_DIR / "nghi_dinh_168_2024_clean.txt"
    output_doc_json = settings.PROCESSED_DIR / "law_document.json"
    output_nd168_json = settings.PROCESSED_DIR / "nghi_dinh_168_document.json"
    output_chunks_jsonl = settings.PROCESSED_DIR / "chunks.jsonl"

    settings.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    logger.info(f"1. Bắt đầu parse Luật 36/2024/QH15: {input_file}")
    parser = DocxLawParser(input_file)
    law_doc = parser.parse()

    with open(output_doc_json, "w", encoding="utf-8") as f:
        json.dump(law_doc.model_dump(), f, ensure_ascii=False, indent=2)

    # Thực hiện Chunking cho Luật 36
    logger.info("2. Chia chunk Luật 36/2024/QH15...")
    chunker = StructureAwareChunker(max_article_chars=1200, max_clause_chars=1000)
    law_chunks = chunker.chunk_document(law_doc)
    logger.info(f"Số chunks Luật 36/2024/QH15: {len(law_chunks)}")

    all_chunks = list(law_chunks)

    # Parse và Chunking Nghị định 168/2024/NĐ-CP (mức phạt tiền & trừ điểm GPLX)
    if nd168_file.exists():
        logger.info(f"3. Bắt đầu parse Nghị định 168/2024/NĐ-CP: {nd168_file}")
        nd_parser = TextLawParser(
            file_path=nd168_file,
            document_id="nghi_dinh_168_2024",
            law_name="Nghị định quy định xử phạt vi phạm hành chính về trật tự, an toàn giao thông trong lĩnh vực giao thông đường bộ; trừ điểm, phục hồi điểm giấy phép lái xe",
            law_number="168/2024/NĐ-CP",
            issue_date="26/12/2024",
            effective_date="01/01/2025",
        )
        nd_doc = nd_parser.parse()
        with open(output_nd168_json, "w", encoding="utf-8") as f:
            json.dump(nd_doc.model_dump(), f, ensure_ascii=False, indent=2)

        nd_chunks = chunker.chunk_document(nd_doc)
        logger.info(f"Số chunks Nghị định 168/2024/NĐ-CP: {len(nd_chunks)}")
        all_chunks.extend(nd_chunks)

    chunks = all_chunks
    logger.info(f"Tổng số chunks toàn hệ thống: {len(chunks)}")

    # Ghi ra file chunks.jsonl
    with open(output_chunks_jsonl, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk.model_dump(), ensure_ascii=False) + "\n")
    logger.info(f"Đã lưu chunks vào: {output_chunks_jsonl}")

    # Kiểm tra dữ liệu sau chunking
    print("\n" + "=" * 60)
    print("BÁO CÁO KIỂM TRA CHUNKING (LUẬT 36 + NGHỊ ĐỊNH 168)")
    print("=" * 60)
    print(f"- Tổng số chunks: {len(chunks)} (Luật 36: {len(law_chunks)}, NĐ 168: {len(chunks) - len(law_chunks)})")

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

    # Kiểm tra truy ngược về 89 Điều của Luật 36
    covered_articles = set(c.article_number for c in law_chunks)
    print(f"- Số Điều Luật 36 được bao phủ: {len(covered_articles)} / 89")
    missing_articles = [x for x in range(1, 90) if x not in covered_articles]
    assert len(missing_articles) == 0, f"Lỗi: Thiếu Điều Luật 36 trong chunks: {missing_articles}"

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
