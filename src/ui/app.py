import base64
import os
import sys
from pathlib import Path
import httpx
import streamlit as st

# Thêm thư mục gốc vào sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Đồng bộ biến môi trường từ Streamlit Secrets (khi deploy trên Streamlit Cloud)
try:
    for _k, _v in st.secrets.items():
        if isinstance(_v, str) and _k not in os.environ:
            os.environ[_k] = _v
except Exception:
    pass

from src.common.config import get_settings
from src.generation.generator import LegalRAGAssistant
from src.ingestion.chunker import StructureAwareChunker
from src.ingestion.docx_parser import DocxLawParser
from src.ingestion.text_parser import TextLawParser
from src.retrieval.bm25_search import BM25SearchEngine
from src.retrieval.hybrid_search import HybridSearchEngine

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="Cổng Tra Cứu Pháp Luật Giao Thông Đường Bộ Việt Nam",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

FASTAPI_URL = "http://localhost:8000"
BG_IMAGE_PATH = Path(__file__).resolve().parent / "assets" / "legal_bg.jpg"


@st.cache_data(show_spinner=False)
def _load_bg_base64(image_path: Path) -> str:
    if not image_path.exists():
        return ""
    return base64.b64encode(image_path.read_bytes()).decode("utf-8")


def _inject_legal_theme():
    """Áp dụng giao diện pháp lý trang trọng với nền ảnh Luật Giao thông Đường bộ Việt Nam."""
    bg_b64 = _load_bg_base64(BG_IMAGE_PATH)
    bg_css = (
        f'background-image: linear-gradient(135deg, rgba(8, 16, 34, 0.80) 0%, rgba(12, 20, 40, 0.84) 55%, rgba(20, 12, 18, 0.82) 100%), '
        f'url("data:image/jpeg;base64,{bg_b64}");'
        if bg_b64
        else "background: linear-gradient(135deg, #0b1528 0%, #16213e 100%);"
    )

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Merriweather:wght@700;900&family=Be+Vietnam+Pro:wght@400;500;600;700&display=swap');

        /* Ẩn các thành phần thừa của Streamlit */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        .stDeployButton {{display: none;}}
        header[data-testid="stHeader"] {{
            background: transparent;
        }}

        /* Nền chính toàn trang */
        .stApp {{
            {bg_css}
            background-size: cover;
            background-position: center center;
            background-attachment: fixed;
            font-family: 'Be Vietnam Pro', sans-serif;
            color: #f1f5f9;
        }}

        /* Sidebar trang trọng kiểu tư pháp */
        section[data-testid="stSidebar"] {{
            background: rgba(10, 18, 36, 0.90) !important;
            border-right: 1px solid rgba(212, 175, 55, 0.35);
            backdrop-filter: blur(10px);
        }}
        section[data-testid="stSidebar"] * {{
            color: #f1f5f9;
        }}

        /* Banner tiêu đề pháp lý */
        .legal-header {{
            background: linear-gradient(90deg, rgba(127, 29, 29, 0.88) 0%, rgba(15, 23, 42, 0.90) 100%);
            border: 1px solid rgba(212, 175, 55, 0.55);
            border-left: 5px solid #d4af37;
            border-radius: 10px;
            padding: 1.25rem 1.6rem;
            margin-bottom: 1.2rem;
            box-shadow: 0 8px 28px rgba(0, 0, 0, 0.45);
            backdrop-filter: blur(8px);
        }}
        .legal-header-emblem {{
            font-size: 0.78rem;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: #f5d061;
            font-weight: 700;
            margin-bottom: 0.3rem;
        }}
        .legal-header-title {{
            font-family: 'Merriweather', Georgia, serif;
            font-size: 1.65rem;
            font-weight: 900;
            color: #ffffff;
            margin: 0 0 0.35rem 0;
            line-height: 1.3;
        }}
        .legal-header-sub {{
            font-size: 0.92rem;
            color: #cbd5e1;
            margin: 0;
        }}

        /* Thẻ văn bản trong sidebar */
        .legal-doc-card {{
            background: rgba(15, 23, 42, 0.75);
            border: 1px solid rgba(212, 175, 55, 0.35);
            border-left: 3px solid #d4af37;
            border-radius: 8px;
            padding: 0.85rem 1rem;
            margin-bottom: 0.8rem;
            font-size: 0.88rem;
            line-height: 1.55;
        }}
        .legal-doc-card strong {{
            color: #f5d061;
        }}

        /* Nút câu hỏi gợi ý */
        div.stButton > button {{
            background: rgba(15, 23, 42, 0.82) !important;
            color: #f8fafc !important;
            border: 1px solid rgba(212, 175, 55, 0.40) !important;
            border-radius: 8px !important;
            padding: 0.6rem 0.9rem !important;
            font-weight: 500 !important;
            text-align: left !important;
            transition: all 0.2s ease !important;
            backdrop-filter: blur(6px);
        }}
        div.stButton > button:hover {{
            background: rgba(127, 29, 29, 0.82) !important;
            border-color: #f5d061 !important;
            color: #ffffff !important;
            transform: translateY(-1px);
        }}

        /* Khung tin nhắn hội thoại */
        div[data-testid="stChatMessage"] {{
            background: rgba(11, 19, 38, 0.86) !important;
            border: 1px solid rgba(212, 175, 55, 0.28);
            border-radius: 10px;
            padding: 1rem 1.2rem;
            margin-bottom: 0.8rem;
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
        }}

        /* Expander căn cứ pháp lý */
        details[data-testid="stExpander"] {{
            background: rgba(15, 23, 42, 0.78) !important;
            border: 1px solid rgba(212, 175, 55, 0.30) !important;
            border-radius: 8px !important;
        }}

        /* Thanh nhập câu hỏi */
        div[data-testid="stChatInput"] {{
            background: rgba(10, 18, 36, 0.92) !important;
            border: 1px solid rgba(212, 175, 55, 0.50) !important;
            border-radius: 10px !important;
        }}

        .section-label {{
            color: #f5d061;
            font-weight: 700;
            font-size: 0.9rem;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            margin-bottom: 0.5rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_resource(show_spinner=False)
def load_standalone_assistant():
    """Tải trợ lý pháp lý cục bộ; tự động khởi tạo chỉ mục BM25 nếu chạy trên Streamlit Cloud."""
    settings = get_settings()
    bm25_path = settings.INDEXES_DIR / "bm25_index.pkl"
    bm25 = BM25SearchEngine()

    if bm25_path.exists():
        bm25.load(bm25_path)
    else:
        chunker = StructureAwareChunker(max_article_chars=1200, max_clause_chars=1000)
        chunks = []
        law_docx = settings.INPUT_DIR / "luat_giao_thong_2024_clean.docx"
        if law_docx.exists():
            chunks.extend(chunker.chunk_document(DocxLawParser(law_docx).parse()))

        nd168_txt = settings.INPUT_DIR / "nghi_dinh_168_2024_clean.txt"
        if nd168_txt.exists():
            nd_doc = TextLawParser(
                file_path=nd168_txt,
                document_id="nghi_dinh_168_2024",
                law_name="Nghị định quy định xử phạt vi phạm hành chính về trật tự, an toàn giao thông trong lĩnh vực giao thông đường bộ; trừ điểm, phục hồi điểm giấy phép lái xe",
                law_number="168/2024/NĐ-CP",
                issue_date="26/12/2024",
                effective_date="01/01/2025",
            ).parse()
            chunks.extend(chunker.chunk_document(nd_doc))

        bm25.build_index(chunks)

    # Chỉ nạp Vector Search nếu đã có Qdrant local index và đủ thư viện (chế độ local)
    vector = None
    qdrant_dir = Path(settings.QDRANT_PATH)
    if qdrant_dir.exists() and any(qdrant_dir.iterdir()):
        try:
            from src.retrieval.vector_search import VectorSearchEngine
            vector = VectorSearchEngine()
        except Exception:
            vector = None

    hybrid = HybridSearchEngine(bm25_engine=bm25, vector_engine=vector)
    return LegalRAGAssistant(hybrid_engine=hybrid)


def check_api_server() -> bool:
    try:
        r = httpx.get(f"{FASTAPI_URL}/health", timeout=1.0)
        return r.status_code == 200
    except Exception:
        return False


def query_backend(prompt: str) -> dict:
    if check_api_server():
        try:
            r = httpx.post(
                f"{FASTAPI_URL}/api/v1/chat",
                json={"query": prompt, "top_k": 5},
                timeout=45.0,
            )
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass

    assistant = load_standalone_assistant()
    res = assistant.answer_question(prompt)
    return res.model_dump()


def render_legal_sources(meta: dict):
    """Hiển thị trích dẫn căn cứ pháp lý (không hiển thị bất kỳ thông số kỹ thuật nào)."""
    scope = meta.get("scope_status")
    sources = meta.get("sources", [])

    if scope == "out_of_scope":
        st.caption("🚫 Nội dung ngoài phạm vi văn bản pháp luật giao thông hiện hành.")
        return

    if sources:
        with st.expander(f"📜 Căn cứ pháp lý trích dẫn ({len(sources)} điều khoản)"):
            for s in sources:
                cl_txt = f", Khoản {s.get('clause_number')}" if s.get("clause_number") else ""
                pt_txt = f", Điểm {s.get('point')}" if s.get("point") else ""
                doc_num = s.get("law_number", "36/2024/QH15")
                doc_label = "Nghị định 168/2024/NĐ-CP" if "168" in doc_num else f"Luật {doc_num}"
                st.markdown(
                    f"**[{doc_label}] Điều {s.get('article_number')}{cl_txt}{pt_txt} — {s.get('article_title')}**"
                )
                st.markdown(f"> {s.get('raw_content', '')}")
                st.divider()


# Áp dụng theme pháp lý
_inject_legal_theme()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(
        """
        <div style="text-align:center; padding: 0.5rem 0 0.8rem 0; border-bottom: 1px solid rgba(212,175,55,0.35); margin-bottom: 1rem;">
            <div style="font-size: 2.2rem;">⚖️</div>
            <div style="font-family: 'Merriweather', Georgia, serif; font-size: 1.15rem; font-weight: 700; color: #f5d061; margin-top: 0.2rem;">
                TRỢ LÝ PHÁP LUẬT
            </div>
            <div style="font-size: 0.78rem; color: #cbd5e1; letter-spacing: 1px; text-transform: uppercase;">
                Giao Thông Đường Bộ Việt Nam
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-label">📚 Văn bản áp dụng</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="legal-doc-card">
            <strong>1. Luật Trật tự, an toàn giao thông đường bộ</strong><br/>
            • Số hiệu: 36/2024/QH15<br/>
            • Hiệu lực: 01/01/2025<br/>
            • Nội dung: Quy tắc giao thông, hành vi bị cấm, giấy phép lái xe.
        </div>
        <div class="legal-doc-card">
            <strong>2. Nghị định xử phạt vi phạm hành chính</strong><br/>
            • Số hiệu: 168/2024/NĐ-CP<br/>
            • Hiệu lực: 01/01/2025<br/>
            • Nội dung: Mức tiền phạt cụ thể, trừ điểm và phục hồi điểm GPLX.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-label">⚖️ Lưu ý pháp lý</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="legal-doc-card" style="border-left-color: #991b1b;">
            Thông tin tra cứu chỉ mang tính chất tham khảo dựa trên văn bản pháp luật hiện hành, không thay thế văn bản hướng dẫn hoặc quyết định chính thức của cơ quan có thẩm quyền.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🗑️ Xóa phiên tra cứu", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- MAIN CONTENT ---
st.markdown(
    """
    <div class="legal-header">
        <div class="legal-header-emblem">⚖️ Cộng hòa Xã hội Chủ nghĩa Việt Nam • Pháp luật Giao thông Đường bộ</div>
        <h1 class="legal-header-title">Cổng Tra Cứu Luật Giao Thông & Mức Xử Phạt 2025</h1>
        <p class="legal-header-sub">
            Tra cứu nhanh quy định, điều khoản và mức xử phạt vi phạm hành chính theo Luật 36/2024/QH15 và Nghị định 168/2024/NĐ-CP.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Câu hỏi gợi ý
st.markdown('<div class="section-label">💡 Tình huống tra cứu phổ biến</div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    if st.button("⚖️ Uống rượu bia lái xe máy bị phạt bao nhiêu tiền?", use_container_width=True):
        st.session_state.sample_query = "Uống rượu bia lái xe máy bị phạt bao nhiêu tiền?"
    if st.button("🪪 Bằng lái xe hạng A1 được điều khiển loại xe nào?", use_container_width=True):
        st.session_state.sample_query = "Bằng lái hạng A1 được điều khiển loại xe nào?"
with col2:
    if st.button("🚦 Vượt đèn đỏ bằng ô tô bị phạt bao nhiêu tiền?", use_container_width=True):
        st.session_state.sample_query = "Vượt đèn đỏ bằng ô tô bị phạt bao nhiêu tiền?"
    if st.button("📋 Giấy phép lái xe có bao nhiêu điểm và trừ thế nào?", use_container_width=True):
        st.session_state.sample_query = "Giấy phép lái xe có bao nhiêu điểm và khi bị trừ hết điểm thì xử lý thế nào?"

# Hiển thị lịch sử hội thoại
for msg in st.session_state.messages:
    avatar = "👤" if msg["role"] == "user" else "⚖️"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if "meta" in msg and msg["meta"]:
            render_legal_sources(msg["meta"])

# Xử lý câu hỏi mới
user_input = st.chat_input("Nhập câu hỏi hoặc tình huống giao thông cần tra cứu...")
query_to_run = None

if "sample_query" in st.session_state and st.session_state.sample_query:
    query_to_run = st.session_state.sample_query
    st.session_state.sample_query = None
elif user_input:
    query_to_run = user_input

if query_to_run:
    st.session_state.messages.append({"role": "user", "content": query_to_run})
    with st.chat_message("user", avatar="👤"):
        st.markdown(query_to_run)

    with st.chat_message("assistant", avatar="⚖️"):
        with st.spinner("Đang đối chiếu văn bản pháp luật..."):
            res = query_backend(query_to_run)
            answer_text = res.get("answer", "Xin lỗi, hiện chưa thể tra cứu câu hỏi này.")
            st.markdown(answer_text)
            render_legal_sources(res)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer_text,
            "meta": res,
        }
    )
