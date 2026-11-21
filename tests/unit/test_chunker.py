import pytest
from src.common.config import get_settings
from src.ingestion.chunker import StructureAwareChunker
from src.ingestion.docx_parser import DocxLawParser


def test_chunker_covers_all_articles():
    settings = get_settings()
    input_file = settings.INPUT_DIR / "luat_giao_thong_2024_clean.docx"
    parser = DocxLawParser(input_file)
    law_doc = parser.parse()

    chunker = StructureAwareChunker(max_article_chars=1200, max_clause_chars=1000)
    chunks = chunker.chunk_document(law_doc)

    assert len(chunks) > 100

    # Tất cả 89 Điều phải có trong chunks
    articles_in_chunks = set(c.article_number for c in chunks)
    assert len(articles_in_chunks) == 89
    for i in range(1, 90):
        assert i in articles_in_chunks

    # Kiểm tra tính toàn vẹn của metadata
    for c in chunks:
        assert c.id
        assert c.law_number == "36/2024/QH15"
        assert c.chapter_number in range(1, 10)
        assert c.chapter_title
        assert c.article_title
        assert len(c.text) > 20
        # Ngữ cảnh phải chứa tên Luật và tiêu đề Điều
        assert c.article_title in c.text


def test_cross_reference_extraction():
    from src.ingestion.cross_ref import extract_cross_references
    text = "Người lái xe phải tuân thủ quy định tại khoản 2 Điều này và Điều 58 của Luật này."
    refs = extract_cross_references(text, current_article=10)
    assert "Khoản 2 Điều 10" in refs
    assert "Điều 58" in refs
