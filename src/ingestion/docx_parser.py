import re
from pathlib import Path
from typing import List, Optional
from docx import Document

from src.common.logger import get_logger
from src.ingestion.models import (
    ArticleData,
    ChapterData,
    ClauseData,
    LawDocument,
    PointData,
)

logger = get_logger("docx_parser")

ROMAN_NUMERALS = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
    "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10,
    "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15,
}


def parse_roman_numeral(roman_str: str) -> int:
    """Chuyển số La Mã sang số nguyên."""
    roman_clean = roman_str.strip().upper()
    if roman_clean in ROMAN_NUMERALS:
        return ROMAN_NUMERALS[roman_clean]
    try:
        return int(roman_clean)
    except ValueError:
        return 0


class DocxLawParser:
    """Bộ bóc tách cấu trúc văn bản Luật từ file DOCX."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.doc: Optional[Document] = None

    def clean_text(self, text: str) -> str:
        """Làm sạch khoảng trắng mà không làm mất ký tự toán học, so sánh và dấu câu."""
        text = text.strip()
        # Chuẩn hóa khoảng trắng dư thừa
        text = re.sub(r"[ \t]+", " ", text)
        return text

    def parse(self) -> LawDocument:
        """Đọc và chuyển đổi toàn bộ file DOCX thành LawDocument có cấu trúc."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"Không tìm thấy file: {self.file_path}")

        self.doc = Document(self.file_path)
        paragraphs = [self.clean_text(p.text) for p in self.doc.paragraphs if p.text.strip()]

        law_doc = LawDocument()

        # Nhận diện thông tin tiêu đề và số hiệu (dòng 0 & 1)
        if len(paragraphs) >= 2:
            law_doc.law_name = paragraphs[0]
            header_meta = paragraphs[1]
            m_law_num = re.search(r"Luật số:\s*([^|]+)", header_meta, re.IGNORECASE)
            if m_law_num:
                law_doc.law_number = m_law_num.group(1).strip()
            m_issue = re.search(r"Ban hành:\s*([^|]+)", header_meta, re.IGNORECASE)
            if m_issue:
                law_doc.issue_date = m_issue.group(1).strip()
            m_eff = re.search(r"Hiệu lực:\s*(.+)$", header_meta, re.IGNORECASE)
            if m_eff:
                law_doc.effective_date = m_eff.group(1).strip()

        # Regex mẫu
        re_chapter = re.compile(r"^(?:CHƯƠNG|Chương)\s+([IVXLCDM0-9]+)\b[.:\s]*(.*)$")
        re_article = re.compile(r"^(?:ĐIỀU|Điều)\s+(\d+)[.:\s]*(.*)$")
        re_clause = re.compile(r"^(\d+)\.\s*(.*)$")
        re_point = re.compile(r"^([a-zđ])\)\s*(.*)$")

        current_chapter: Optional[ChapterData] = None
        current_article: Optional[ArticleData] = None
        current_clause: Optional[ClauseData] = None

        i = 2
        while i < len(paragraphs):
            line = paragraphs[i]

            # 1. Nhận diện Chương
            m_chap = re_chapter.match(line)
            if m_chap:
                ch_roman = m_chap.group(1)
                ch_num = parse_roman_numeral(ch_roman)
                inline_title = m_chap.group(2).strip()

                # Tiêu đề chương có thể nằm ngay trên dòng hoặc ở dòng tiếp theo
                ch_title = inline_title
                if not ch_title and (i + 1) < len(paragraphs):
                    next_line = paragraphs[i + 1]
                    if not re_article.match(next_line) and not re_chapter.match(next_line):
                        ch_title = next_line
                        i += 1

                current_chapter = ChapterData(
                    chapter_number=ch_num,
                    chapter_title=ch_title,
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
                    article_title=art_title,
                    text="",
                )
                if current_chapter is None:
                    # Trường hợp điều xuất hiện trước khi có chương
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

                current_clause.points.append(
                    PointData(point=point_char, text=point_text)
                )
                i += 1
                continue

            # 5. Dòng văn bản bình thường (preamble của Điều không đánh số Khoản, hoặc nối dài)
            if current_article is not None:
                if current_clause is not None:
                    if current_clause.points:
                        # Nối tiếp vào điểm cuối
                        current_clause.points[-1].text += " " + line
                    else:
                        current_clause.text += " " + line
                else:
                    # Điều chỉ có 1 đoạn văn không đánh số Khoản (ví dụ Điều 1)
                    if not current_article.clauses:
                        current_clause = ClauseData(
                            clause_number=None,
                            text=line,
                            points=[],
                        )
                        current_article.clauses.append(current_clause)
                    else:
                        current_article.clauses[-1].text += " " + line

            i += 1

        # Cập nhật trường text tổng thể cho mỗi Điều
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

        self._validate(law_doc)
        return law_doc

    def _validate(self, law_doc: LawDocument):
        """Kiểm tra tính toàn vẹn của dữ liệu sau khi parse."""
        num_chapters = len(law_doc.chapters)
        total_articles = sum(len(ch.articles) for ch in law_doc.chapters)
        logger.info(f"Kết quả parse: {num_chapters} Chương, {total_articles} Điều.")

        if num_chapters != 9:
            logger.warning(f"Số lượng Chương ({num_chapters}) khác 9 dự kiến!")

        if total_articles != 89:
            logger.warning(f"Số lượng Điều ({total_articles}) khác 89 dự kiến!")

        # Kiểm tra tính liên tục của các Điều
        all_art_nums = [
            art.article_number
            for ch in law_doc.chapters
            for art in ch.articles
        ]
        missing = [x for x in range(1, 90) if x not in all_art_nums]
        if missing:
            raise ValueError(f"Thiếu các Điều sau trong văn bản: {missing}")
