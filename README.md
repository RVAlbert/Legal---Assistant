# VN-Legal RAG Assistant ⚖️🚦

**Hệ thống Trợ lý Tra cứu Pháp luật Giao thông Đường bộ Việt Nam (Luật số 36/2024/QH15 & Nghị định số 168/2024/NĐ-CP) ứng dụng kiến trúc RAG (Retrieval-Augmented Generation).**

---

## 📌 1. Giới thiệu tổng quan

Hệ thống hỗ trợ tra cứu chính xác quy tắc giao thông, hành vi bị nghiêm cấm, phân hạng/điểm giấy phép lái xe và **mức xử phạt tiền cụ thể** dựa trên 2 văn bản pháp luật chính thức có hiệu lực từ **01/01/2025**:

1. **Luật Trật tự, an toàn giao thông đường bộ số 36/2024/QH15** (9 Chương, 89 Điều — 500 chunks).
2. **Nghị định số 168/2024/NĐ-CP** quy định xử phạt vi phạm hành chính & trừ điểm, phục hồi điểm GPLX (4 Chương, 55 Điều — 768 chunks).

### Tính năng nổi bật
- **Tìm kiếm lai kết hợp (Hybrid Search):** Hợp nhất `BM25Plus` (từ khóa tiếng Việt + mở rộng từ ngữ đời thường) và `BAAI/bge-m3` + `Qdrant Vector DB` qua thuật toán **Reciprocal Rank Fusion (RRF)** trên tổng cộng **1,268 chunks**.
- **Structure-Aware Chunking:** Bảo toàn cấu trúc Chương – Điều – Khoản – Điểm, gắn siêu dữ liệu tên văn bản và trích xuất tham chiếu chéo.
- **AI Skill trả lời ngắn gọn, đúng trọng tâm:** Cấu hình skill tại `src/generation/skills/concise_legal_answer.md` giúp tiết kiệm token, trả lời thẳng kết luận kèm trích dẫn chính xác `[Tên văn bản, Điều X, khoản Y, điểm Z]`.
- **Phân luồng thông minh:** Tự động phân biệt câu hỏi pháp lý, giao tiếp xã hội thân thiện và các câu lạc đề/ngoài phạm vi.
- **Giao diện pháp lý trang trọng:** Streamlit UI tùy biến phong cách tư pháp nghiêm chỉnh, ẩn toàn bộ thông số kỹ thuật đối với người dùng cuối.

---

## 🏗️ 2. Kiến trúc hệ thống

```text
[Người dùng]
    │
    ▼
[Streamlit Legal UI (Port 8501)]  <──>  [FastAPI Backend (Port 8000)]
    │
    ▼
[Scope Validator] ──> (Giao tiếp xã hội / Lạc đề / Ngoài phạm vi)
    │ (Câu hỏi pháp lý giao thông)
    ▼
┌───────────────────────────────────────────────────┐
│               HYBRID SEARCH ENGINE                │
│  QueryExpander -> BM25Plus + Qdrant BGE-M3 -> RRF │
│        (1,268 chunks: Luật 36 + NĐ 168)           │
└───────────────────────────────────────────────────┘
    │
    ▼
[Cross-Reference Expander] + [Context Builder & AI Skill]
    │
    ▼
[LLM Engine (Groq Qwen 3.8 27B / OpenRouter Fallback)]
    │
    ▼
[Citation Validator] -> [Câu trả lời ngắn gọn kèm Căn cứ pháp lý]
```

---

## 🚀 3. Cài đặt và Khởi chạy

### 3.1. Cài đặt môi trường
Yêu cầu: Python >= 3.11.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3.2. Cấu hình biến môi trường
```bash
cp .env.example .env
```
Điền API Key của bạn vào `.env` (khuyên dùng **Groq** tốc độ cao, hoặc **OpenRouter**):
```env
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
GROQ_MODEL=qwen/qwen3.8-27b
```

### 3.3. Nạp dữ liệu & Xây dựng chỉ mục
```bash
# 1. Parse Luật 36/2024/QH15 + Nghị định 168/2024/NĐ-CP -> 1,268 chunks
python scripts/run_ingestion.py

# 2. Xây dựng BM25 và Qdrant Vector index (thêm CUDA_VISIBLE_DEVICES="" nếu chạy CPU)
python scripts/build_indexes.py
```

### 3.4. Khởi chạy Ứng dụng
- **Giao diện Web (Streamlit):**
  ```bash
  streamlit run src/ui/app.py
  ```
  Truy cập: `http://localhost:8501`

- **API Server (FastAPI):**
  ```bash
  uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
  ```
  Swagger Docs: `http://localhost:8000/docs`

---

## 🧪 4. Kiểm thử

```bash
pytest tests/
```
