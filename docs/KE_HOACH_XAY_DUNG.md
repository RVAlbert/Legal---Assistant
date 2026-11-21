# Kế hoạch xây dựng VN Legal RAG Assistant

**Phiên bản:** 1.0  
**Phạm vi:** MVP tra cứu Luật Trật tự, an toàn giao thông đường bộ số 36/2024/QH15  
**Frontend:** Streamlit  
**Backend:** FastAPI  
**LLM:** OpenRouter  
**Ngày cập nhật:** 21/11/2026

## 1. Mục tiêu và kiến trúc đã chốt

Hệ thống có hai luồng:

- **Luồng offline:** đọc file luật, làm sạch, phân tích cấu trúc, chia chunk, tạo embedding và tạo chỉ mục.
- **Luồng online:** nhận câu hỏi, tìm kiếm nguồn, mở rộng tham chiếu chéo, gọi LLM qua OpenRouter và trả lời có trích dẫn.

Kiến trúc chính:

```text
Streamlit
    ↓ HTTP
FastAPI
    ↓
Scope Validator
    ↓
BM25 + Qdrant Vector Search
    ↓
RRF Fusion
    ↓
Cross-reference Expansion
    ↓
Context Builder
    ↓
OpenRouter LLM
    ↓
Citation Validator
    ↓
Streamlit
```

## 2. Công nghệ và thuật toán

| Thành phần | Lựa chọn cho MVP | Mục đích |
|---|---|---|
| Ngôn ngữ | Python | Dùng chung cho ingestion, backend, retrieval và evaluation |
| Frontend | Streamlit | Xây giao diện hỏi đáp nhanh |
| Backend | FastAPI + Uvicorn | Cung cấp API và tách logic khỏi giao diện |
| Đọc DOCX | `python-docx` | Đọc file luật đầu vào |
| Phân tích cấu trúc | Parser tự viết | Nhận diện Chương, Điều, Khoản, Điểm |
| Chia đoạn | Structure-Aware Chunking | Giữ đúng cấu trúc pháp luật |
| Embedding | `BAAI/bge-m3` | Tìm kiếm theo ngữ nghĩa tiếng Việt |
| Vector database | Qdrant | Lưu và tìm vector cùng metadata |
| Tìm kiếm từ khóa | BM25 với `rank-bm25` | Tìm số Điều, thuật ngữ và con số chính xác |
| Hợp nhất kết quả | Reciprocal Rank Fusion | Kết hợp BM25 và Semantic Search |
| LLM | Model được chọn trên OpenRouter | Tổng hợp câu trả lời từ context |
| Kiểm thử | pytest | Kiểm tra từng tầng và nghiệm thu |

## 3. Các bước thực hiện

### Bước 1: Chuẩn bị môi trường và cấu hình dự án

Đầu vào:

- Cây thư mục dự án.
- Lựa chọn công nghệ ở mục 2.
- File luật sẽ đặt tại `data/input/`.

Việc cần làm:

1. Chọn phiên bản Python tương thích.
2. Tạo môi trường ảo riêng cho dự án.
3. Khai báo dependency trong `pyproject.toml`.
4. Tạo `.env.example` cho cấu hình OpenRouter, Qdrant và retrieval.
5. Tạo `.gitignore` để không đưa API key, môi trường ảo và dữ liệu sinh ra vào Git.
6. Kiểm tra các lệnh chạy cơ bản của môi trường.

Kết quả:

- Có thể cài dependency mà không ảnh hưởng dự án khác.
- Có nơi cấu hình API nhưng không lưu API key thật trong mã nguồn.
- Các bước cài đặt được ghi lại và có thể lặp lại.

### Bước 2: Kiểm tra file luật đầu vào

File sử dụng:

```text
data/input/luat_giao_thong_2024_clean.docx
```

Việc cần làm:

1. Kiểm tra file có mở được không.
2. Đếm số đoạn, bảng và ký tự.
3. Kiểm tra file có đủ Chương và Điều dự kiến không.
4. Phát hiện đoạn rỗng, ký hiệu bị mất hoặc ký tự bất thường.
5. Không sửa trực tiếp file gốc.

Kết quả:

Một báo cáo kiểm tra dữ liệu trước khi bắt đầu xử lý.

### Bước 3: Đọc và làm sạch DOCX

Việc cần làm:

1. Đọc đoạn văn và bảng bằng `python-docx`.
2. Chuẩn hóa khoảng trắng và xuống dòng.
3. Giữ nguyên số, dấu câu, ký hiệu toán học và đơn vị đo.
4. Lưu dữ liệu trung gian vào `data/processed/`.

Kết quả:

Văn bản sạch nhưng chưa chia thành chunk tìm kiếm.

### Bước 4: Phân tích cấu trúc pháp luật

Việc cần làm:

1. Nhận diện Chương.
2. Nhận diện Điều và tiêu đề Điều.
3. Nhận diện Khoản.
4. Nhận diện Điểm.
5. Kiểm tra thứ tự và các mục bị thiếu.
6. Gắn thông tin vị trí vào từng đơn vị dữ liệu.

Kết quả:

Mỗi phần nội dung biết được nó thuộc Chương, Điều, Khoản và Điểm nào.

### Bước 5: Chia văn bản bằng Structure-Aware Chunking

Quy tắc:

1. Giữ trọn một Điều nếu độ dài cho phép.
2. Điều dài được tách theo Khoản.
3. Khoản dài được tách theo Điểm hoặc nhóm câu.
4. Không cắt giữa câu nếu không cần thiết.
5. Mỗi chunk lặp lại tiêu đề Điều cha.

Kết quả:

```text
data/processed/chunks.jsonl
```

Mỗi dòng là một chunk có nội dung và metadata.

### Bước 6: Kiểm tra dữ liệu sau chunking

Việc cần làm:

1. Kiểm tra số lượng chunk.
2. Kiểm tra chunk rỗng.
3. Kiểm tra metadata.
4. Kiểm tra khả năng truy ngược về văn bản gốc.
5. Kiểm tra các ký hiệu và con số quan trọng.

Chỉ chuyển sang tạo index sau khi bước này đạt.

### Bước 7: Tạo BM25 Keyword Index

Việc cần làm:

1. Đọc nội dung từ `chunks.jsonl`.
2. Tokenize tiếng Việt theo quy tắc phù hợp.
3. Xây dựng BM25 index.
4. Lưu dữ liệu cần thiết để khởi tạo lại index.

Mục tiêu:

- Tìm chính xác số Điều.
- Tìm đúng thuật ngữ pháp lý.
- Tìm đúng con số, đơn vị và hạng giấy phép.

### Bước 8: Tạo Embedding và Qdrant Index

Việc cần làm:

1. Dùng `BAAI/bge-m3` tạo vector cho từng chunk.
2. Tạo collection trong Qdrant.
3. Lưu vector cùng metadata.
4. Kiểm tra số vector bằng số chunk.
5. Chạy thử một số câu hỏi mẫu.

Kết quả:

Qdrant có thể tìm các chunk gần nghĩa với câu hỏi.

### Bước 9: Xây dựng Semantic Search

Luồng xử lý:

```text
Câu hỏi
→ Embedding câu hỏi
→ Tìm vector gần nhất trong Qdrant
→ Lấy chunk và metadata
```

Kết quả cần trả về:

- `chunk_id`;
- điểm tìm kiếm;
- nội dung;
- Điều/Khoản/Điểm;
- thông tin văn bản.

### Bước 10: Xây dựng Hybrid Search bằng RRF

Luồng xử lý:

```text
Câu hỏi
├── BM25 Search
└── Semantic Search
        ↓
    RRF Fusion
        ↓
Danh sách chunk đã hợp nhất
```

Việc cần làm:

1. Lấy danh sách kết quả từ BM25.
2. Lấy danh sách kết quả từ Qdrant.
3. Quy đổi thứ hạng bằng RRF.
4. Gom chunk trùng nhau.
5. Sắp xếp kết quả cuối.

### Bước 11: Phân loại phạm vi câu hỏi

Phân thành ba trạng thái:

1. **Answered:** có đủ nguồn để trả lời.
2. **Insufficient data:** đúng lĩnh vực nhưng cần văn bản chưa nạp.
3. **Out of scope:** ngoài phạm vi hệ thống.

Không dùng một ngưỡng điểm vector duy nhất để quyết định trạng thái.

### Bước 12: Xử lý tham chiếu chéo

Việc cần làm:

1. Nhận diện “Điều”, “Khoản”, “Điểm” được dẫn chiếu.
2. Tìm thêm phần được dẫn chiếu.
3. Giới hạn số lượng nguồn bổ sung.
4. Gắn nhãn nguồn chính và nguồn tham chiếu.
5. Cảnh báo nếu tham chiếu đến văn bản chưa được nạp.

### Bước 13: Xây dựng Context Builder

Chỉ đưa vào LLM:

- câu hỏi;
- các chunk liên quan;
- nguồn tham chiếu chéo cần thiết;
- quy tắc trả lời;
- quy tắc trích dẫn;
- quy tắc từ chối.

Không gửi toàn bộ văn bản luật cho mỗi câu hỏi.

### Bước 14: Kết nối OpenRouter

OpenRouter được gọi thông qua API tương thích OpenAI:

```text
Base URL: https://openrouter.ai/api/v1
```

Cấu hình cần có:

- `OPENROUTER_API_KEY`;
- `OPENROUTER_MODEL`;
- `OPENROUTER_BASE_URL`.

API key thật chỉ được đặt trong file `.env` hoặc secret của môi trường triển khai. Không ghi key vào Git, file kế hoạch hoặc mã nguồn.

Nên tạo lớp `LLMProvider` để backend không phụ thuộc cứng vào một model hoặc một nhà cung cấp.

### Bước 15: Sinh câu trả lời có kiểm soát

LLM phải:

1. Chỉ dùng nội dung trong context.
2. Trả lời bằng tiếng Việt.
3. Gắn trích dẫn cho ý pháp lý.
4. Nêu điều kiện và ngoại lệ nếu có.
5. Không tự tạo mức phạt hoặc số Điều.
6. Nêu rõ khi dữ liệu chưa đủ.

### Bước 16: Kiểm tra câu trả lời và trích dẫn

Backend kiểm tra:

1. Có câu trả lời hay không.
2. Có trích dẫn hay không.
3. Trích dẫn có tồn tại trong nguồn truy xuất không.
4. Điều/Khoản/Điểm có hợp lệ không.
5. Câu trả lời có thông tin ngoài context không.
6. Có mức phạt hoặc kết luận chưa có căn cứ không.

Nếu không đạt, hệ thống trả cảnh báo hoặc yêu cầu sinh lại một lần.

### Bước 17: Xây dựng API FastAPI

Các endpoint MVP:

```text
GET  /health
GET  /api/v1/documents
POST /api/v1/search
POST /api/v1/chat
```

`/search` dùng để kiểm tra retrieval độc lập. `/chat` dùng cho giao diện người dùng.

### Bước 18: Xây dựng giao diện Streamlit

Giao diện cần có:

- ô nhập câu hỏi;
- câu hỏi mẫu;
- câu trả lời;
- trích dẫn;
- nội dung nguồn;
- cảnh báo thiếu dữ liệu;
- lịch sử hội thoại trong phiên;
- thông tin văn bản và phiên bản.

Streamlit chỉ gọi API FastAPI và hiển thị kết quả.

### Bước 19: Viết kiểm thử

Kiểm thử theo tầng:

1. Dữ liệu DOCX.
2. Parser cấu trúc.
3. Chunking.
4. BM25.
5. Semantic Search.
6. RRF.
7. Scope Validator.
8. Citation Validator.
9. API.
10. Giao diện.

### Bước 20: Chạy bộ đánh giá nghiệm thu

Đánh giá tối thiểu:

- độ chính xác tìm kiếm;
- độ chính xác trích dẫn;
- khả năng trả lời đúng nguồn;
- khả năng từ chối ngoài phạm vi;
- khả năng cảnh báo thiếu văn bản;
- thời gian phản hồi;
- lỗi khi dịch vụ ngoài không hoạt động.

### Bước 21: Đóng gói và triển khai

Chỉ thực hiện sau khi MVP chạy ổn định:

1. Đóng gói backend.
2. Đóng gói frontend.
3. Cấu hình Qdrant persistent.
4. Đưa API key vào secret.
5. Chạy kiểm tra health.
6. Kiểm tra lại dữ liệu và index.
7. Triển khai theo môi trường demo.

## 4. Thứ tự ưu tiên khi triển khai

Ưu tiên theo thứ tự:

1. Môi trường.
2. Kiểm tra dữ liệu.
3. Parser.
4. Chunking.
5. BM25.
6. Qdrant và embedding.
7. Hybrid Search.
8. API search.
9. OpenRouter và context.
10. API chat.
11. Streamlit.
12. Evaluation.
13. Deployment.

Không nên làm giao diện trước khi retrieval đã tìm được nguồn đúng.
