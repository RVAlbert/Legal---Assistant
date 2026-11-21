from typing import List
from src.ingestion.cross_ref import extract_cross_references
from src.ingestion.models import ArticleData, ChapterData, LawChunk, LawDocument


class StructureAwareChunker:
    """Bộ chia chunk nhận thức cấu trúc pháp luật theo chuẩn FR-02.

    Quy tắc:
    1. Giữ trọn một Điều nếu độ dài văn bản <= max_article_chars (mặc định 1200 ký tự).
    2. Nếu Điều dài > max_article_chars, chia theo từng Khoản.
    3. Nếu một Khoản có nhiều Điểm và độ dài quá lớn (> max_clause_chars, mặc định 1000 ký tự),
       tách theo từng Điểm hoặc nhóm Điểm.
    4. Mỗi chunk đều có ngữ cảnh đầy đủ: lặp lại Tên Luật, Chương, và Tiêu đề Điều.
    5. Trích xuất danh sách tham chiếu chéo (references) của chunk.
    """

    def __init__(self, max_article_chars: int = 1200, max_clause_chars: int = 1000):
        self.max_article_chars = max_article_chars
        self.max_clause_chars = max_clause_chars

    def chunk_document(self, law_doc: LawDocument) -> List[LawChunk]:
        chunks: List[LawChunk] = []

        for chapter in law_doc.chapters:
            for article in chapter.articles:
                art_chunks = self._chunk_article(law_doc, chapter, article)
                chunks.extend(art_chunks)

        return chunks

    def _chunk_article(
        self,
        law_doc: LawDocument,
        chapter: ChapterData,
        article: ArticleData,
    ) -> List[LawChunk]:
        chunks: List[LawChunk] = []

        header_prefix = (
            f"[{law_doc.law_name}]\n"
            f"Chương {chapter.chapter_number}. {chapter.chapter_title}\n"
            f"Điều {article.article_number}. {article.article_title}\n"
        )

        total_art_len = len(article.text)

        # 1. Trường hợp Điều ngắn hoặc chỉ có 1 Khoản/đoạn: Giữ trọn Điều
        if total_art_len <= self.max_article_chars or len(article.clauses) <= 1:
            raw_text = article.text
            full_text = header_prefix + raw_text
            chunk_id = f"giao_thong_36_2024_dieu_{article.article_number}"
            refs = extract_cross_references(raw_text, current_article=article.article_number)

            clause_num = article.clauses[0].clause_number if article.clauses else None

            chunks.append(
                LawChunk(
                    id=chunk_id,
                    document_id=law_doc.document_id,
                    law_number=law_doc.law_number,
                    law_name=law_doc.law_name,
                    chapter_number=chapter.chapter_number,
                    chapter_title=chapter.chapter_title,
                    article_number=article.article_number,
                    article_title=article.article_title,
                    clause_number=clause_num,
                    point=None,
                    text=full_text,
                    raw_content=raw_text,
                    references=refs,
                )
            )
            return chunks

        # 2. Trường hợp Điều dài: Chia theo từng Khoản
        for clause in article.clauses:
            cl_prefix = f"Khoản {clause.clause_number}. " if clause.clause_number is not None else ""
            cl_body = clause.text
            pts_text = "\n".join(f"{p.point}) {p.text}" for p in clause.points) if clause.points else ""

            raw_clause_content = cl_prefix + cl_body
            if pts_text:
                raw_clause_content += "\n" + pts_text

            # Nếu Khoản không quá dài, giữ trọn Khoản
            if len(raw_clause_content) <= self.max_clause_chars or not clause.points:
                clause_suffix = f"_khoan_{clause.clause_number}" if clause.clause_number is not None else ""
                chunk_id = f"giao_thong_36_2024_dieu_{article.article_number}{clause_suffix}"
                full_text = header_prefix + raw_clause_content
                refs = extract_cross_references(raw_clause_content, current_article=article.article_number)

                chunks.append(
                    LawChunk(
                        id=chunk_id,
                        document_id=law_doc.document_id,
                        law_number=law_doc.law_number,
                        law_name=law_doc.law_name,
                        chapter_number=chapter.chapter_number,
                        chapter_title=chapter.chapter_title,
                        article_number=article.article_number,
                        article_title=article.article_title,
                        clause_number=clause.clause_number,
                        point=None,
                        text=full_text,
                        raw_content=raw_clause_content,
                        references=refs,
                    )
                )
            else:
                # 3. Nếu Khoản dài và có nhiều Điểm: Chia theo từng Điểm
                for pt in clause.points:
                    point_content = f"{cl_prefix}{cl_body}\n{pt.point}) {pt.text}"
                    full_text = header_prefix + point_content
                    chunk_id = f"giao_thong_36_2024_dieu_{article.article_number}_khoan_{clause.clause_number}_diem_{pt.point}"
                    refs = extract_cross_references(point_content, current_article=article.article_number)

                    chunks.append(
                        LawChunk(
                            id=chunk_id,
                            document_id=law_doc.document_id,
                            law_number=law_doc.law_number,
                            law_name=law_doc.law_name,
                            chapter_number=chapter.chapter_number,
                            chapter_title=chapter.chapter_title,
                            article_number=article.article_number,
                            article_title=article.article_title,
                            clause_number=clause.clause_number,
                            point=pt.point,
                            text=full_text,
                            raw_content=f"{pt.point}) {pt.text}",
                            references=refs,
                        )
                    )

        return chunks
