"""Script kiểm tra và khảo sát file luật DOCX đầu vào (Bước 2)."""

import re
import sys
from pathlib import Path

# Thêm thư mục gốc dự án vào sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from docx import Document
from src.common.config import get_settings
from src.common.logger import setup_logger

logger = setup_logger("inspect_docx")


def inspect_docx(file_path: Path):
    if not file_path.exists():
        logger.error(f"File không tồn tại: {file_path}")
        sys.exit(1)

    logger.info(f"Bắt đầu khảo sát file: {file_path.name} ({file_path.stat().st_size} bytes)")
    doc = Document(file_path)

    paragraphs = doc.paragraphs
    tables = doc.tables

    total_paragraphs = len(paragraphs)
    total_tables = len(tables)

    empty_paragraphs = 0
    non_empty_paragraphs = []
    total_chars = 0

    for i, p in enumerate(paragraphs):
        text = p.text.strip()
        if not text:
            empty_paragraphs += 1
        else:
            non_empty_paragraphs.append((i, text))
            total_chars += len(text)

    # Patterns
    # Chương: "Chương I", "CHƯƠNG I", "Chương 1", etc.
    re_chapter = re.compile(r"^(?:CHƯƠNG|Chương)\s+([IVXLCDM0-9]+)\b[.:\s]*(.*)$", re.IGNORECASE)
    # Điều: "Điều 1.", "Điều 1:", "Điều 1 "
    re_article = re.compile(r"^(?:ĐIỀU|Điều)\s+(\d+)[.:\s]*(.*)$", re.IGNORECASE)
    # Khoản: "1. ", "2. "
    re_clause = re.compile(r"^(\d+)\.\s+(.*)$")
    # Điểm: "a) ", "b) "
    re_point = re.compile(r"^([a-zđ])\)\s+(.*)$", re.IGNORECASE)

    chapters_found = []
    articles_found = []
    clauses_count = 0
    points_count = 0

    # Kiểm tra ký tự toán học, so sánh
    symbols = {"<": 0, ">": 0, "≤": 0, "≥": 0, "%": 0, "/": 0}

    for idx, text in non_empty_paragraphs:
        m_ch = re_chapter.match(text)
        if m_ch:
            chapters_found.append((m_ch.group(1), m_ch.group(2).strip(), idx))

        m_art = re_article.match(text)
        if m_art:
            art_num = int(m_art.group(1))
            art_title = m_art.group(2).strip()
            articles_found.append((art_num, art_title, idx))

        if re_clause.match(text):
            clauses_count += 1
        if re_point.match(text):
            points_count += 1

        for s in symbols:
            symbols[s] += text.count(s)

    # Phân tích articles
    art_nums = [a[0] for a in articles_found]
    unique_art_nums = sorted(list(set(art_nums)))
    missing_articles = []
    if unique_art_nums:
        for expected in range(1, max(unique_art_nums) + 1):
            if expected not in unique_art_nums:
                missing_articles.append(expected)

    duplicate_articles = [x for x in art_nums if art_nums.count(x) > 1]

    print("\n" + "=" * 60)
    print("BÁO CÁO KHẢO SÁT FILE LUẬT ĐẦU VÀO")
    print("=" * 60)
    print(f"- Đường dẫn: {file_path}")
    print(f"- Kích thước: {file_path.stat().st_size:,} bytes")
    print(f"- Tổng số đoạn (paragraphs): {total_paragraphs}")
    print(f"  + Đoạn có nội dung: {len(non_empty_paragraphs)}")
    print(f"  + Đoạn rỗng: {empty_paragraphs}")
    print(f"- Tổng số bảng (tables): {total_tables}")
    print(f"- Tổng số ký tự (ước tính): {total_chars:,}")
    print("-" * 60)
    print(f"- Số Chương nhận diện: {len(chapters_found)}")
    for ch_num, ch_title, line_idx in chapters_found:
        print(f"  * Chương {ch_num}: {ch_title} (dòng {line_idx})")
    print("-" * 60)
    print(f"- Số Điều nhận diện: {len(articles_found)}")
    print(f"- Dải Điều: từ Điều {min(art_nums) if art_nums else 0} đến Điều {max(art_nums) if art_nums else 0}")
    print(f"- Số Điều trùng lặp: {len(set(duplicate_articles))} (danh sách: {list(set(duplicate_articles))})")
    print(f"- Số Điều bị thiếu trong khoảng [1..{max(art_nums) if art_nums else 0}]: {len(missing_articles)} {missing_articles}")
    print(f"- Ước tính số Khoản nhận diện theo đầu mục (1., 2., ...): {clauses_count}")
    print(f"- Ước tính số Điểm nhận diện theo đầu mục (a), b), ...): {points_count}")
    print("-" * 60)
    print(f"- Thống kê ký hiệu toán học / so sánh:")
    for sym, count in symbols.items():
        print(f"  '{sym}': {count}")
    print("=" * 60)

    # Hiển thị 5 điều đầu tiên và 5 điều cuối cùng
    print("\n5 Điều đầu tiên:")
    for a in articles_found[:5]:
        print(f"  - Điều {a[0]}: {a[1]}")
    print("\n5 Điều cuối cùng:")
    for a in articles_found[-5:]:
        print(f"  - Điều {a[0]}: {a[1]}")
    print("=" * 60 + "\n")

    return {
        "total_paragraphs": total_paragraphs,
        "empty_paragraphs": empty_paragraphs,
        "chapters_count": len(chapters_found),
        "articles_count": len(articles_found),
        "missing_articles": missing_articles,
        "duplicate_articles": duplicate_articles,
    }


if __name__ == "__main__":
    settings = get_settings()
    input_file = settings.INPUT_DIR / "luat_giao_thong_2024_clean.docx"
    inspect_docx(input_file)
