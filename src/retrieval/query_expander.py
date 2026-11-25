import re
from typing import List, Tuple

# Bảng quy đổi lỗi gõ phím, tiếng lóng, viết tắt
TYPO_MAPPINGS: List[Tuple[str, str]] = [
    (r"\bkhôn\b", "không"),
    (r"\b(ko|k|hông|hem|hok)\b", "không"),
    (r"\b(dc|đc)\b", "được"),
    (r"\b(oto|o to)\b", "ô tô"),
    (r"\bxe may\b", "xe máy"),
    (r"\bgplx\b", "giấy phép lái xe"),
    (r"\bcsgt\b", "cảnh sát giao thông"),
]

# Bảng ánh xạ ngữ nghĩa từ ngữ đời thường sang thuật ngữ pháp lý
COLLOQUIAL_SEMANTIC_MAPPINGS: List[Tuple[str, str]] = [
    # Nhậu, rượu bia, nồng độ cồn
    (
        r"\b(nhậu|nhậu nhẹt|uống rượu|uống bia|say xỉn|say rượu|uống cồn|có cồn|có men|uống 1 giọt|uống một ít bia|uống một ít rượu|làm vài lon|làm cốc bia|uống chén|cụng ly)\b",
        "nồng độ cồn trong máu hoặc hơi thở rượu bia hành vi bị nghiêm cấm",
    ),
    # Hỏi mức phạt tiền / xe máy
    (
        r"\b(phạt bao nhiêu|phạt bao nhiu|bị phạt|mức phạt|tiền phạt|phạt mấy triệu|bao nhiu tiền|bao nhiêu tiền)\b",
        "phạt tiền từ đồng đến đồng trừ điểm giấy phép lái xe 168/2024/NĐ-CP",
    ),
    (
        r"\b(xe máy|xe gắn máy)\b",
        "xe mô tô xe gắn máy",
    ),
    # Đèn tín hiệu giao thông
    (
        r"\b(vượt đèn đỏ|vượt đèn vàng|vượt đèn|đèn đỏ|đèn vàng)\b",
        "không chấp hành hiệu lệnh của đèn tín hiệu giao thông đèn màu đỏ cấm đi",
    ),
    # Tốc độ
    (
        r"\b(bắn tốc độ|chạy quá tốc độ|phóng nhanh|chạy ẩu|quá tốc độ|vượt tốc độ)\b",
        "tốc độ tối đa cho phép chấp hành quy định về tốc độ",
    ),
    # Số người chở trên xe máy
    (
        r"\b(kẹp 3|kẹp ba|chở 3|chở ba|chở 4|chở bốn|kẹp bốn|chở quá số người)\b",
        "số người được chở trên xe mô tô xe gắn máy",
    ),
    # Mũ bảo hiểm
    (
        r"\b(mũ bảo hiểm|nón bảo hiểm|không đội mũ|không đội nón|mũ cối)\b",
        "đội mũ bảo hiểm cài quai đúng quy cách xe mô tô xe gắn máy",
    ),
    # Điện thoại khi lái xe
    (
        r"\b(dùng điện thoại|sử dụng điện thoại|nghe điện thoại|lướt điện thoại|bấm điện thoại)\b",
        "dùng tay cầm và sử dụng điện thoại hành vi bị nghiêm cấm",
    ),
    # Vòng xuyến
    (
        r"\b(vòng xuyến|bùng binh)\b",
        "nhường đường tại nơi đường giao nhau có báo hiệu đi theo vòng xuyến",
    ),
    # Xe ưu tiên
    (
        r"\b(xe cứu thương|xe cứu hỏa|xe công an|xe ưu tiên|cứu thương|xe cảnh sát)\b",
        "quyền ưu tiên và nhường đường cho xe ưu tiên",
    ),
    # Trẻ em ngồi ô tô
    (
        r"\b(trẻ em|ghế phụ|ghế trước|ghế phụ trước)\b",
        "trẻ em dưới 10 tuổi và chiều cao dưới 1,35 mét chở trẻ em trên xe ô tô",
    ),
    # Điểm GPLX
    (
        r"\b(trừ điểm|phục hồi điểm|bao nhiêu điểm|hết điểm|trừ hết điểm)\b",
        "điểm của giấy phép lái xe 12 điểm trừ điểm phục hồi điểm",
    ),
    # Giấy phép lái xe
    (
        r"\b(bằng lái|bằng xe|bằng ô tô|bằng xe máy|bằng a1|bằng b1|bằng b2|bằng b)\b",
        "giấy phép lái xe phân hạng giấy phép lái xe",
    ),
]


class QueryExpander:
    """Bộ chuẩn hóa và mở rộng ngữ nghĩa câu hỏi đời thường (Query Expander)."""

    @classmethod
    def expand(cls, query: str) -> str:
        text = query.strip()

        # 1. Chuẩn hóa viết tắt và lỗi chính tả phổ biến
        for pattern, replacement in TYPO_MAPPINGS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # 2. Ánh xạ ngữ nghĩa đời thường sang thuật ngữ pháp luật tương ứng
        expansions = []
        for pattern, legal_terms in COLLOQUIAL_SEMANTIC_MAPPINGS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                expansions.append(legal_terms)

        if expansions:
            # Ghép thêm các thuật ngữ pháp lý trọng tâm vào câu truy vấn
            expanded_query = f"{text} {' '.join(expansions)}"
            return expanded_query

        return text
