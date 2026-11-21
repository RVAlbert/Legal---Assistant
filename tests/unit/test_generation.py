import pytest
from src.generation.citation_validator import CitationValidator
from src.generation.context_builder import ContextBuilder
from src.generation.models import ScopeStatus
from src.generation.scope_validator import ScopeValidator
from src.retrieval.models import SearchResult


def test_scope_validator_out_of_scope():
    validator = ScopeValidator()

    # Câu hỏi về Luật Lao động
    check1 = validator.assess_pre_retrieval("Thời gian thử việc theo Luật Lao động là bao lâu?")
    assert check1 is not None
    assert check1.status == ScopeStatus.OUT_OF_SCOPE
    assert "Luật Lao động" in check1.reason or "luật lao động" in check1.reason

    # Câu hỏi lập trình
    check2 = validator.assess_pre_retrieval("Viết giúp tôi một đoạn code python")
    assert check2 is not None
    assert check2.status == ScopeStatus.OUT_OF_SCOPE

    # Câu hỏi rỗng
    check3 = validator.assess_pre_retrieval("   ")
    assert check3 is not None
    assert check3.status == ScopeStatus.OUT_OF_SCOPE


def test_scope_validator_insufficient_data():
    validator = ScopeValidator()
    results = [
        SearchResult(
            chunk_id="dieu_10", score=0.03, rank=1,
            document_id="doc", law_number="36", law_name="Luật",
            chapter_number=2, chapter_title="Quy tắc",
            article_number=10, article_title="Quy tắc chung",
            text="Phải chấp hành đèn tín hiệu.", raw_content="Đèn tín hiệu",
        )
    ]

    # Hỏi về tiền phạt
    check = validator.assess_post_retrieval("Vượt đèn đỏ bị phạt bao nhiêu tiền?", results)
    assert check.status == ScopeStatus.INSUFFICIENT_DATA
    assert "Nghị định" in check.reason


def test_scope_validator_answered():
    validator = ScopeValidator()
    results = [
        SearchResult(
            chunk_id="dieu_9", score=0.03, rank=1,
            document_id="doc", law_number="36", law_name="Luật",
            chapter_number=1, chapter_title="Chung",
            article_number=9, article_title="Hành vi cấm",
            clause_number=2, point=None,
            text="Cấm lái xe khi trong máu có cồn.", raw_content="Cấm có cồn",
        )
    ]
    check = validator.assess_post_retrieval("Uống rượu có được lái xe không?", results)
    assert check.status == ScopeStatus.ANSWERED


def test_citation_validator():
    validator = CitationValidator()
    sources = [
        SearchResult(
            chunk_id="c1", score=0.03, rank=1,
            document_id="doc", law_number="36", law_name="Luật",
            chapter_number=1, chapter_title="Chung",
            article_number=9, article_title="Hành vi cấm",
            text="Điều 9", raw_content="Điều 9",
        )
    ]

    # Câu trả lời trích dẫn đúng Điều 9
    ans_valid = "Theo quy định tại [Điều 9, khoản 2], người lái xe không được có nồng độ cồn."
    citations, warnings = validator.validate_citations(ans_valid, sources)
    assert len(citations) == 1
    assert citations[0].article_number == 9
    assert citations[0].is_valid is True
    assert len(warnings) == 0

    # Câu trả lời bịa Điều 999 (không có trong sources)
    ans_hallucinated = "Căn cứ vào [Điều 999], bạn bị phạt tù."
    citations_bad, warnings_bad = validator.validate_citations(ans_hallucinated, sources)
    assert len(citations_bad) == 1
    assert citations_bad[0].article_number == 999
    assert citations_bad[0].is_valid is False
    assert len(warnings_bad) > 0


def test_context_builder_format():
    builder = ContextBuilder()
    sources = [
        SearchResult(
            chunk_id="c1", score=0.03, rank=1,
            document_id="doc", law_number="36", law_name="Luật",
            chapter_number=4, chapter_title="GPLX",
            article_number=58, article_title="Điểm GPLX",
            clause_number=1, point=None,
            text="Điều 58. Điểm giấy phép lái xe", raw_content="Điểm GPLX",
        )
    ]
    messages = builder.build_prompt(
        query="Điểm GPLX là gì?",
        primary_sources=sources,
        expansion_sources=[],
        scope_status=ScopeStatus.ANSWERED,
    )
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "Điều 58" in messages[1]["content"]
    assert "Điểm GPLX là gì?" in messages[1]["content"]
