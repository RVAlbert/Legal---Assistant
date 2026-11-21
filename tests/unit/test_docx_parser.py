import pytest
from src.common.config import get_settings
from src.ingestion.docx_parser import DocxLawParser, parse_roman_numeral


def test_parse_roman_numeral():
    assert parse_roman_numeral("I") == 1
    assert parse_roman_numeral("IV") == 4
    assert parse_roman_numeral("IX") == 9
    assert parse_roman_numeral("10") == 10


def test_docx_parser_reads_full_law():
    settings = get_settings()
    input_file = settings.INPUT_DIR / "luat_giao_thong_2024_clean.docx"
    parser = DocxLawParser(input_file)
    law_doc = parser.parse()

    assert law_doc.law_number == "36/2024/QH15"
    assert "Giao thông" in law_doc.law_name or "GIAO THÔNG" in law_doc.law_name
    assert len(law_doc.chapters) == 9

    total_articles = sum(len(ch.articles) for ch in law_doc.chapters)
    assert total_articles == 89

    # Kiểm tra Điều 1 (phạm vi điều chỉnh)
    dieu_1 = law_doc.chapters[0].articles[0]
    assert dieu_1.article_number == 1
    assert "Phạm vi điều chỉnh" in dieu_1.article_title
    assert len(dieu_1.text) > 0

    # Kiểm tra Điều 89 (quy định chuyển tiếp)
    dieu_89 = law_doc.chapters[-1].articles[-1]
    assert dieu_89.article_number == 89
    assert "chuyển tiếp" in dieu_89.article_title.lower()
