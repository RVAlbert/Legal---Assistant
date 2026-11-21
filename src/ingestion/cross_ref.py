import re
from typing import List


def extract_cross_references(text: str, current_article: int | None = None) -> List[str]:
    """Trích xuất các tham chiếu pháp lý trong đoạn văn bản.

    Ví dụ:
    - 'theo quy định tại Điều 58' -> 'Điều 58'
    - 'khoản 2 Điều 10' -> 'Khoản 2 Điều 10'
    - 'khoản 2 Điều này' -> 'Khoản 2 Điều {current_article}'
    - 'Chương II' -> 'Chương II'
    """
    refs = set()

    # Mẫu: khoản X Điều Y
    clause_article_pattern = re.compile(
        r"khoản\s+(\d+)\s+Điều\s+(\d+)", re.IGNORECASE
    )
    for m in clause_article_pattern.finditer(text):
        c_num, a_num = m.group(1), m.group(2)
        refs.add(f"Khoản {c_num} Điều {a_num}")

    # Mẫu: khoản X Điều này
    if current_article is not None:
        clause_this_art_pattern = re.compile(
            r"khoản\s+(\d+)\s+Điều\s+này", re.IGNORECASE
        )
        for m in clause_this_art_pattern.finditer(text):
            c_num = m.group(1)
            refs.add(f"Khoản {c_num} Điều {current_article}")

    # Mẫu: Điều X
    article_pattern = re.compile(r"Điều\s+(\d+)", re.IGNORECASE)
    for m in article_pattern.finditer(text):
        a_num = int(m.group(1))
        # Không tự tham chiếu chính Điều hiện tại trừ khi đi kèm khoản
        if a_num != current_article:
            refs.add(f"Điều {a_num}")

    # Mẫu: Chương X
    chapter_pattern = re.compile(r"Chương\s+([IVXLCDM]+)", re.IGNORECASE)
    for m in chapter_pattern.finditer(text):
        ch_num = m.group(1).upper()
        refs.add(f"Chương {ch_num}")

    return sorted(list(refs))
