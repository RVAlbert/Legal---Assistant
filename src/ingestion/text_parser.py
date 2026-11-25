import re
from pathlib import Path
from typing import Optional

from src.common.logger import get_logger
from src.ingestion.docx_parser import parse_roman_numeral
from src.ingestion.models import (
    ArticleData,
    ChapterData,
    ClauseData,
    LawDocument,
    PointData,
)

logger = get_logger("text_parser")


class TextLawParser:
    """Bộ bóc tách cấu trúc văn bản pháp luật (Luật / Nghị định) từ file văn bản thuần (TXT)."""

    def __init__(
        self,
        file_path: Path,
        document_id: str,
        law_name: str,
        law_number: str,
        issue_date: str = "",
        effective_date: str = "",
    ):
        self.file_path = file_path
        self.document_id = document_id
        self.law_name = law_name
        self.law_number = law_number
        self.issue_date = issue_date
        self.effective_date = effective_date

    def clean_text(self, text: str) -> str:
        text = text.strip()
        return re.sub(r"[ \t]+", " ", text)

    def parse(self) -> LawDocument:
        if not self.file_path.exists():
            raise FileNotFoundError(f"Không tìm thấy file: {self.file_path}")

        raw_lines = self.file_path.read_text(encoding="utf-8").splitlines()
        paragraphs = [self.clean_text(ln) for ln in raw_lines if ln.strip()]

        law_doc = LawDocument(
            document_id=self.document_id,
            law_name=self.law_name,
            law_number=self.law_number,
            issue_date=self.issue_date,
            effective_date=self.effective_date,
        )

        re_chapter = re.compile(r"^(?:CHƯƠNG|Chương)\s+([IVXLCDM0-9]+)\b[.:\s]*(.*)$")
        re_article = re.compile(r"^(?:ĐIỀU|Điều)\s+(\d+)[.:\s]*(.*)$")
        re_clause = re.compile(r"^(\d+)\.\s*(.*)$")
        re_point = re.compile(r"^([a-zđ])\)\s*(.*)$")
        re_section = re.compile(r"^(?:Mục|MỤC)\s+\d+\b")

        current_chapter: Optional[ChapterData] = None
        current_article: Optional[ArticleData] = None
        current_clause: Optional[ClauseData] = None

        i = 2 if len(paragraphs) > 2 else 0
        while i < len(paragraphs):
            line = paragraphs[i]

            # Bỏ qua dòng tiêu đề Mục nếu nằm ngoài Điều
            if re_section.match(line) and current_article is None:
                i += 1
                continue

            # 1. Nhận diện Chương
            m_chap = re_chapter.match(line)
            if m_chap:
                ch_num = parse_roman_numeral(m_chap.group(1))
                ch_title = m_chap.group(2).strip()
                if not ch_title and (i + 1) < len(paragraphs):
                    next_line = paragraphs[i + 1]
                    if not re_article.match(next_line) and not re_chapter.match(next_line):
                        ch_title = next_line
                        i += 1

                current_chapter = ChapterData(
                    chapter_number=ch_num,
                    chapter_title=ch_title or f"Chương {ch_num}",
                )
                law_doc.chapters.append(current_chapter)
                current_article = None
                current_clause = None
                i += 1
                continue

            # 2. Nhận diện Điều
            m_art = re_article.match(line)
            if m_art:
                art_num = int(m_art.group(1))
                art_title = m_art.group(2).strip()

                current_article = ArticleData(
                    article_number=art_num,
                    article_title=art_title or f"Điều {art_num}",
                    text="",
                )
                if current_chapter is None:
                    current_chapter = ChapterData(chapter_number=1, chapter_title="QUY ĐỊNH CHUNG")
                    law_doc.chapters.append(current_chapter)

                current_chapter.articles.append(current_article)
                current_clause = None
                i += 1
                continue

            # 3. Nhận diện Khoản
            m_clause = re_clause.match(line)
            if m_clause and current_article is not None:
                clause_num = int(m_clause.group(1))
                clause_body = m_clause.group(2).strip()
                current_clause = ClauseData(
                    clause_number=clause_num,
                    text=clause_body,
                    points=[],
                )
                current_article.clauses.append(current_clause)
                i += 1
                continue

            # 4. Nhận diện Điểm
            m_pt = re_point.match(line)
            if m_pt and current_clause is not None:
                point_char = m_pt.group(1).lower()
                point_text = m_pt.group(2).strip()
                current_clause.points.append(PointData(point=point_char, text=point_text))
                i += 1
                continue

            # 5. Dòng nối tiếp
            if current_article is not None:
                if current_clause is not None:
                    if current_clause.points:
                        current_clause.points[-1].text += " " + line
                    else:
                        current_clause.text += " " + line
                else:
                    if not current_article.clauses:
                        current_clause = ClauseData(clause_number=None, text=line, points=[])
                        current_article.clauses.append(current_clause)
                    else:
                        current_article.clauses[-1].text += " " + line

            i += 1

        # Ghép text tổng thể cho từng Điều
        for ch in law_doc.chapters:
            for art in ch.articles:
                art_texts = []
                for cl in art.clauses:
                    prefix = f"{cl.clause_number}. " if cl.clause_number is not None else ""
                    cl_full = prefix + cl.text
                    if cl.points:
                        pts_str = "\n".join(f"{p.point}) {p.text}" for p in cl.points)
                        cl_full += "\n" + pts_str
                    art_texts.append(cl_full)
                art.text = "\n".join(art_texts)

        total_articles = sum(len(ch.articles) for ch in law_doc.chapters)
        logger.info(
            f"Đã parse {self.law_number}: {len(law_doc.chapters)} Chương, {total_articles} Điều."
        )
        return law_doc
