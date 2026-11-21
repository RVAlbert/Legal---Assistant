"""Script chạy thử nghiệm toàn bộ luồng RAG Assistant (Giai đoạn 4)."""

import sys
import time
from pathlib import Path

# Thêm thư mục gốc vào sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.common.config import get_settings
from src.common.logger import setup_logger
from src.generation.generator import LegalRAGAssistant
from src.retrieval.bm25_search import BM25SearchEngine
from src.retrieval.hybrid_search import HybridSearchEngine
from src.retrieval.vector_search import VectorSearchEngine

logger = setup_logger("test_rag_pipeline")


def main():
    settings = get_settings()
    bm25_index_file = settings.INDEXES_DIR / "bm25_index.pkl"

    logger.info("1. Khởi tạo BM25 & Qdrant Search Engine...")
    bm25_engine = BM25SearchEngine()
    bm25_engine.load(bm25_index_file)

    vector_engine = VectorSearchEngine()

    logger.info("2. Khởi tạo Hybrid Search Engine...")
    hybrid_engine = HybridSearchEngine(bm25_engine=bm25_engine, vector_engine=vector_engine)

    logger.info("3. Khởi tạo LegalRAGAssistant với model OpenRouter...")
    assistant = LegalRAGAssistant(hybrid_engine=hybrid_engine)

    test_cases = [
        (
            "TC-01 (Tình huống đời thường - Đúng phạm vi)",
            "Uống ít bia mà trong hơi thở vẫn có cồn thì có được lái xe không?",
        ),
        (
            "TC-05 (Quy định trực tiếp - Đúng phạm vi)",
            "Giấy phép lái xe có bao nhiêu điểm và cách trừ điểm như thế nào?",
        ),
        (
            "TC-07 (Hỏi tiền phạt - Thiếu dữ liệu Nghị định)",
            "Vượt đèn đỏ bằng ô tô bị phạt bao nhiêu tiền?",
        ),
        (
            "TC-08 (Ngoài phạm vi - Luật Lao động)",
            "Thời gian thử việc tối đa theo Luật Lao động là bao nhiêu tháng?",
        ),
        (
            "TC-10 (Ngoài phạm vi - Lập trình)",
            "Viết giúp tôi một chương trình Python để tính toán ma trận.",
        ),
    ]

    print("\n" + "=" * 75)
    print("CHẠY THỬ TOÀN DIỆN HỆ THỐNG TRỢ LÝ PHÁP LUẬT VN-LEGAL RAG ASSISTANT")
    print("=" * 75)

    for tc_name, question in test_cases:
        print(f"\n>>> [{tc_name}]")
        print(f"Câu hỏi: {question}")
        t0 = time.time()
        response = assistant.answer_question(question)
        latency = (time.time() - t0) * 1000

        print(f"- Trạng thái phạm vi: {response.scope_status.value.upper()}")
        print(f"- Thời gian phản hồi: {latency:.1f}ms")
        print(f"- Số nguồn sử dụng: {len(response.sources)} chính, {len(response.expansion_sources)} tham chiếu")
        if response.citations:
            cits = [f"Điều {c.article_number}" + (f", k.{c.clause_number}" if c.clause_number else "") for c in response.citations]
            print(f"- Trích dẫn phát hiện: {', '.join(cits)}")
        if response.warnings:
            print(f"- Cảnh báo: {response.warnings}")

        print("\n--- CÂU TRẢ LỜI CỦA TRỢ LÝ ---")
        print(response.answer)
        print("-" * 75)

    print("\nHoàn tất thử nghiệm toàn diện Giai đoạn 4!\n")


if __name__ == "__main__":
    main()
