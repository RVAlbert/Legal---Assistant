# VN-Legal RAG Assistant 🚦⚖️

**Hệ thống Trợ lý Tra cứu Luật Trật tự, an toàn giao thông đường bộ Việt Nam (Luật số 36/2024/QH15) bằng mô hình RAG (Retrieval-Augmented Generation).**

---

## 📌 1. Giới thiệu tổng quan

Hệ thống được thiết kế chuyên biệt để giải quyết các vấn đề cốt lõi trong tra cứu văn bản pháp luật Việt Nam:
1. **Tìm kiếm lai kết hợp (Hybrid Search):** Hợp nhất giữa tìm kiếm từ khóa chính xác (`BM25Plus`) và tìm kiếm ngữ nghĩa sâu (`BAAI/bge-m3` + `Qdrant Vector DB`) qua thuật toán **Reciprocal Rank Fusion (RRF)**.
2. **Structure-Aware Chunking:** Phân đoạn văn bản nhận thức cấu trúc Chương - Điều - Khoản - Điểm, lặp lại ngữ cảnh tiêu đề, giữ trọn ý nghĩa pháp lý (tổng cộng 500 chunks tối ưu).
3. **Phân loại phạm vi & Kiểm duyệt trích dẫn chặt chẽ:** Tự động phát hiện câu hỏi ngoài phạm vi (`OUT_OF_SCOPE`) hoặc thiếu dữ liệu mức tiền phạt (`INSUFFICIENT_DATA`), ép trích dẫn chính xác `[Điều X, khoản Y]` và ngăn chặn triệt để ảo giác (Hallucination).
4. **Mô hình ngôn ngữ thế hệ mới:** Tích hợp trực tiếp với OpenRouter LLM (`nvidia/nemotron-3-ultra-550b-a55b:free`).

---

## 🏗️ 2. Kiến trúc hệ thống

```text
[Người dùng]
    │
    ▼
[Streamlit Frontend (Port 8501)]
    │ HTTP / Python
    ▼
[FastAPI Backend (Port 8000)]
    │
    ▼
[Scope Validator] ── (Ngoài phạm vi) ──> [Từ chối ngay lập tức (0ms)]
    │ (Hợp lệ)
    ▼
┌──────────────────────────────────────────────┐
│            HYBRID SEARCH ENGINE              │
│  BM25Plus (Từ khóa) + Qdrant BGE-M3 (Vector)  │
│                      ↓                       │
│          Reciprocal Rank Fusion (RRF)        │
└──────────────────────────────────────────────┘
    │
    ▼
[Cross-Reference Expander] (Tự động mở rộng Điều dẫn chiếu)
    │
    ▼
[Context Builder] (Đóng gói Prompt & Căn cứ pháp lý)
    │
    ▼
[OpenRouter LLM (NVIDIA Nemotron 3 Ultra)]
    │
    ▼
[Citation Validator] (Kiểm tra chéo tính xác thực của Điều/Khoản)
    │
    ▼
[Trả lời người dùng kèm Căn cứ & Thông số kỹ thuật]
```

---

## 🚀 3. Cài đặt và Khởi chạy

### 3.1. Cài đặt môi trường
Yêu cầu: Python >= 3.11, < 3.15.

```bash
# Tạo môi trường ảo
python3 -m venv .venv
source .venv/bin/activate

# Cài đặt toàn bộ dependencies
pip install -e ".[dev]"
```

### 3.2. Cấu hình biến môi trường
Tạo file `.env` từ `.env.example`:
```bash
cp .env.example .env
```
Điền OpenRouter API Key vào `.env`:
```env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxx
OPENROUTER_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free
```

### 3.3. Xử lý dữ liệu & Tạo chỉ mục
```bash
# 1. Parse văn bản và tạo chunks
python scripts/run_ingestion.py

# 2. Xây dựng BM25 và Vector index vào Qdrant
python scripts/build_indexes.py
```

### 3.4. Khởi chạy Ứng dụng

* **Cách 1: Khởi chạy Giao diện Web Streamlit (Khuyên dùng):**
  ```bash
  .venv/bin/streamlit run src/ui/app.py
  ```
  Truy cập: `http://localhost:8501`

* **Cách 2: Khởi chạy FastAPI Backend:**
  ```bash
  .venv/bin/uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
  ```
  Tài liệu Swagger API: `http://localhost:8000/docs`

---

## 🧪 4. Kiểm thử & Đánh giá Nghiệm thu

* **Chạy toàn bộ Unit Tests & Integration Tests:**
  ```bash
  .venv/bin/pytest tests/
  ```

* **Chạy bộ Benchmark Nghiệm thu 25 câu hỏi chuẩn (FR-08):**
  ```bash
  .venv/bin/python scripts/run_evaluation.py
  ```
  Báo cáo chi tiết được lưu tại: `data/evaluation/evaluation_report.md`.
