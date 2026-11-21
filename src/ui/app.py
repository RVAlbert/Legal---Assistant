import json
import sys
import time
from pathlib import Path
import httpx
import streamlit as st

# Thêm thư mục gốc vào sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.common.config import get_settings
from src.generation.generator import LegalRAGAssistant
from src.generation.models import ScopeStatus
from src.retrieval.bm25_search import BM25SearchEngine
from src.retrieval.hybrid_search import HybridSearchEngine
from src.retrieval.vector_search import VectorSearchEngine

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="VN-Legal RAG Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

FASTAPI_URL = "http://localhost:8000"


@st.cache_resource(show_spinner=False)
def load_standalone_assistant():
    """Tải assistant trực tiếp nếu FastAPI chưa chạy."""
    settings = get_settings()
    bm25 = BM25SearchEngine()
    bm25.load(settings.INDEXES_DIR / "bm25_index.pkl")
    vector = VectorSearchEngine()
    hybrid = HybridSearchEngine(bm25_engine=bm25, vector_engine=vector)
    return LegalRAGAssistant(hybrid_engine=hybrid)


def check_api_server() -> bool:
    """Kiểm tra xem FastAPI backend có đang chạy hay không."""
    try:
        r = httpx.get(f"{FASTAPI_URL}/health", timeout=1.0)
        return r.status_code == 200
    except Exception:
        return False


def query_backend(prompt: str) -> dict:
    """Gửi câu hỏi tới FastAPI backend (hoặc fallback sang local assistant)."""
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

    # Fallback chạy local
    assistant = load_standalone_assistant()
    res = assistant.answer_question(prompt)
    return res.model_dump()


# --- SIDEBAR ---
with st.sidebar:
    st.title("⚖️ Trợ lý Pháp luật")
    st.caption("Phiên bản MVP 1.1")

    st.markdown("---")
    st.subheader("📚 Văn bản tra cứu")
    st.info(
        """
        **Luật Trật tự, an toàn giao thông đường bộ**  
        - **Số hiệu:** 36/2024/QH15  
        - **Ban hành:** 27/06/2024  
        - **Hiệu lực:** 01/01/2025  
        - **Quy mô:** 9 Chương, 89 Điều
        """
    )

    st.subheader("⚙️ Cấu hình hệ thống")
    settings = get_settings()
    is_api_online = check_api_server()
    st.write(f"- **Backend API:** {'🟢 Online (Port 8000)' if is_api_online else '🟠 Local Direct'}")
    st.write(f"- **LLM:** `{settings.OPENROUTER_MODEL}`")
    st.write(f"- **Embedding:** `{settings.EMBEDDING_MODEL}`")
    st.write(f"- **Chỉ mục:** 500 chunks (BM25 + Qdrant)")

    st.markdown("---")
    st.subheader("⚠️ Phạm vi & Giới hạn")
    st.warning(
        """
        - Hệ thống **chỉ hỗ trợ** Luật 36/2024/QH15.  
        - **Mức tiền phạt cụ thể** thuộc Nghị định xử phạt vi phạm hành chính (chưa bao gồm trong dữ liệu hiện tại).  
        - Không thay thế tư vấn pháp lý chính thức từ cơ quan nhà nước hoặc luật sư.
        """
    )

    if st.button("🗑️ Xóa lịch sử tra cứu", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- MAIN CONTENT ---
st.title("🚦 Trợ lý Tra cứu Luật Trật tự, an toàn giao thông đường bộ 2024")
st.markdown(
    "Hệ thống hỏi đáp pháp lý thông minh dựa trên kiến trúc **RAG (Retrieval-Augmented Generation)**: "
    "kết hợp tìm kiếm từ khóa BM25, tìm kiếm ngữ nghĩa BGE-M3 và kiểm duyệt trích dẫn chặt chẽ."
)

# Khởi tạo session state cho lịch sử
if "messages" not in st.session_state:
    st.session_state.messages = []

# Câu hỏi gợi ý
st.markdown("**💡 Câu hỏi mẫu:**")
col1, col2 = st.columns(2)
with col1:
    if st.button("🍺 Có một ít cồn trong hơi thở thì có được lái xe không?", use_container_width=True):
        st.session_state.sample_query = "Uống ít bia mà trong hơi thở vẫn có cồn thì có được lái xe không?"
    if st.button("🪪 Bằng lái xe hạng A1 được điều khiển loại xe nào?", use_container_width=True):
        st.session_state.sample_query = "Bằng lái hạng A1 được điều khiển loại xe nào?"
with col2:
    if st.button("⭐ Giấy phép lái xe có bao nhiêu điểm và trừ thế nào?", use_container_width=True):
        st.session_state.sample_query = "Giấy phép lái xe có bao nhiêu điểm và khi bị trừ hết điểm thì xử lý thế nào?"
    if st.button("🚦 Vượt đèn đỏ bằng ô tô bị phạt bao nhiêu tiền?", use_container_width=True):
        st.session_state.sample_query = "Vượt đèn đỏ bằng ô tô bị phạt bao nhiêu tiền?"

# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "meta" in msg and msg["meta"]:
            m = msg["meta"]
            # Badge trạng thái
            scope = m.get("scope_status")
            if scope == "answered":
                st.success("✅ Đầy đủ căn cứ trong Luật 36/2024/QH15")
            elif scope == "insufficient_data":
                st.warning("⚠️ Đúng lĩnh vực nhưng thiếu dữ liệu mức tiền phạt (thuộc Nghị định)")
            elif scope == "out_of_scope":
                st.error("🚫 Ngoài phạm vi văn bản hỗ trợ")

            # Căn cứ pháp lý mở rộng
            sources = m.get("sources", [])
            if sources:
                with st.expander(f"📑 Căn cứ pháp lý & Trích dẫn nguồn ({len(sources)} nguồn)"):
                    for s in sources:
                        cl_txt = f", Khoản {s.get('clause_number')}" if s.get('clause_number') else ""
                        pt_txt = f", Điểm {s.get('point')}" if s.get('point') else ""
                        st.markdown(
                            f"**Điều {s.get('article_number')}{cl_txt}{pt_txt} - {s.get('article_title')}** "
                            f"*(Điểm RRF: {s.get('score', 0):.4f})*"
                        )
                        st.text(s.get("raw_content", ""))
                        st.divider()

            # Thông số kỹ thuật
            with st.expander("⏱️ Thông số kỹ thuật"):
                st.write(f"- Độ trễ: `{m.get('latency_ms', 0):.1f} ms`")
                if m.get("citations"):
                    cits_str = ", ".join(
                        f"Điều {c.get('article_number')}" for c in m.get("citations", [])
                    )
                    st.write(f"- Trích dẫn phát hiện: `{cits_str}`")

# Xử lý input từ chat hoặc từ câu hỏi mẫu
user_input = st.chat_input("Nhập câu hỏi của bạn về Luật Giao thông 2024...")
query_to_run = None

if "sample_query" in st.session_state and st.session_state.sample_query:
    query_to_run = st.session_state.sample_query
    st.session_state.sample_query = None
elif user_input:
    query_to_run = user_input

if query_to_run:
    # Hiển thị tin nhắn người dùng
    st.session_state.messages.append({"role": "user", "content": query_to_run})
    with st.chat_message("user"):
        st.markdown(query_to_run)

    # Hiển thị spinner và gọi xử lý
    with st.chat_message("assistant"):
        with st.spinner("Đang tra cứu cơ sở dữ liệu luật và tổng hợp câu trả lời..."):
            res = query_backend(query_to_run)
            answer_text = res.get("answer", "Xin lỗi, đã xảy ra lỗi trong quá trình xử lý.")
            st.markdown(answer_text)

            scope = res.get("scope_status")
            if scope == "answered":
                st.success("✅ Đầy đủ căn cứ trong Luật 36/2024/QH15")
            elif scope == "insufficient_data":
                st.warning("⚠️ Đúng lĩnh vực nhưng thiếu dữ liệu mức tiền phạt (thuộc Nghị định)")
            elif scope == "out_of_scope":
                st.error("🚫 Ngoài phạm vi văn bản hỗ trợ")

            sources = res.get("sources", [])
            if sources:
                with st.expander(f"📑 Căn cứ pháp lý & Trích dẫn nguồn ({len(sources)} nguồn)"):
                    for s in sources:
                        cl_txt = f", Khoản {s.get('clause_number')}" if s.get('clause_number') else ""
                        pt_txt = f", Điểm {s.get('point')}" if s.get('point') else ""
                        st.markdown(
                            f"**Điều {s.get('article_number')}{cl_txt}{pt_txt} - {s.get('article_title')}** "
                            f"*(Điểm RRF: {s.get('score', 0):.4f})*"
                        )
                        st.text(s.get("raw_content", ""))
                        st.divider()

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer_text,
            "meta": res,
        }
    )
