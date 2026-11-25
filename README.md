<div align="center">

<img src="src/ui/assets/legal_bg.jpg" alt="Cổng Tra Cứu Pháp Luật Giao Thông Đường Bộ Việt Nam" width="100%" />

# ⚖️ VN-Legal Assistant
### Cổng Tra Cứu Pháp Luật Giao Thông Đường Bộ Việt Nam (2025)

**Trợ lý AI hỗ trợ người dân tra cứu nhanh quy định, quyền – nghĩa vụ và mức xử phạt vi phạm hành chính về trật tự, an toàn giao thông đường bộ — ngắn gọn, chính xác và luôn kèm căn cứ pháp lý rõ ràng.**

</div>

---

## 📌 Giới thiệu sản phẩm

**VN-Legal Assistant** là nền tảng hỏi – đáp pháp luật thông minh được thiết kế dành cho người tham gia giao thông tại Việt Nam. Thay vì phải tìm kiếm thủ công qua hàng trăm trang văn bản luật phức tạp, người dùng chỉ cần đặt câu hỏi bằng ngôn ngữ đời thường để nhận ngay câu trả lời **ngắn gọn, đúng trọng tâm và trích dẫn chính xác đến từng Điều, Khoản, Điểm**.

---

## 📚 Văn bản pháp luật áp dụng

Hệ thống cập nhật đồng bộ theo khung pháp lý giao thông đường bộ mới nhất có hiệu lực từ **01/01/2025**:

| Văn bản pháp luật | Số hiệu | Phạm vi hỗ trợ |
| :--- | :---: | :--- |
| **Luật Trật tự, an toàn giao thông đường bộ** | `36/2024/QH15` | Quy tắc giao thông, hành vi bị nghiêm cấm, phân hạng & điểm giấy phép lái xe |
| **Nghị định xử phạt vi phạm hành chính về TTATGT** | `168/2024/NĐ-CP` | Mức tiền phạt cụ thể theo từng hành vi, mức trừ điểm và phục hồi điểm GPLX |

---

## ✨ Điểm nổi bật

- **Hiểu ngôn ngữ tự nhiên đời thường:** Dễ dàng đặt câu hỏi theo cách nói hàng ngày mà không cần nhớ thuật ngữ luật hay số điều khoản.
- **Trả lời ngắn gọn, đi thẳng vào trọng tâm:** Cung cấp kết luận rõ ràng (được phép / bị cấm / khung tiền phạt cụ thể), không lan man dài dòng.
- **Trích dẫn minh bạch, chuẩn xác:** Mọi câu trả lời đều đi kèm nguồn đối chiếu chính thức `[Tên văn bản, Điều X, khoản Y, điểm Z]`.
- **Hiểu đúng ngữ cảnh thực tế:** Phân biệt rõ vai trò người hỏi (người lái xe, người ngồi sau, người đi bộ...) để đưa ra nhận định sát thực tế nhất.
- **Giao diện pháp lý trang trọng:** Thiết kế trực quan, nghiêm chỉnh, thân thiện với mọi đối tượng người dùng.

---

## 💬 Một số tình huống tra cứu tiêu biểu

| Câu hỏi người dùng | Phản hồi từ VN-Legal Assistant |
| :--- | :--- |
| *"Nhậu mà lái xe máy thì bị phạt bao nhiêu tiền?"* | Chia 3 khung tùy nồng độ cồn:<br>• **≤ 50 mg/100ml máu (≤ 0,25 mg/l khí thở):** 2.000.000 – 3.000.000 đồng `[Nghị định 168/2024/NĐ-CP, Điều 7, khoản 6, điểm a]`.<br>• **> 50 – 80 mg/100ml máu (> 0,25 – 0,4 mg/l khí thở):** 6.000.000 – 8.000.000 đồng `[Nghị định 168/2024/NĐ-CP, Điều 7, khoản 8, điểm b]`.<br>• **> 80 mg/100ml máu (> 0,4 mg/l khí thở):** 8.000.000 – 10.000.000 đồng `[Nghị định 168/2024/NĐ-CP, Điều 7, khoản 9, điểm d]`. |
| *"Vượt đèn đỏ bằng ô tô bị phạt bao nhiêu tiền?"* | Phạt tiền từ **18.000.000 đến 20.000.000 đồng** `[Nghị định 168/2024/NĐ-CP, Điều 6, khoản 9, điểm b]`. |
| *"Nhậu mà được người khác chở về thì có bị sao không?"* | **Không bị xử phạt**, vì bạn không trực tiếp điều khiển phương tiện. Quy định cấm chỉ áp dụng cho người **điều khiển phương tiện** có nồng độ cồn `[Luật 36/2024/QH15, Điều 9, khoản 2]`. |

---

## 🚀 Trải nghiệm nhanh

```bash
# 1. Cài đặt môi trường & cấu hình API Key trong file .env (từ .env.example)
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env

# 2. Khởi tạo dữ liệu & mở giao diện tra cứu
python scripts/run_ingestion.py && python scripts/build_indexes.py
streamlit run src/ui/app.py
```

Truy cập ứng dụng tại `http://localhost:8501`.

---

## ⚠️ Lưu ý pháp lý

> Thông tin do hệ thống cung cấp chỉ mang tính chất tham khảo dựa trên văn bản pháp luật hiện hành, không thay thế tư vấn pháp lý chính thức từ luật sư hoặc quyết định của cơ quan có thẩm quyền.
