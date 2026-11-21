# BÁO CÁO NGHIỆM THU CHẤT LƯỢNG RAG ASSISTANT

**Dự án:** VN-Legal RAG Assistant  
**Văn bản:** Luật Trật tự, an toàn giao thông đường bộ số 36/2024/QH15  
**Mô hình LLM:** `nvidia/nemotron-3-ultra-550b-a55b:free`  
**Mô hình Embedding:** `BAAI/bge-m3`  
**Thời gian đánh giá:** 1730.9 ms / câu (trung bình)  

---

## 1. Kết quả tổng hợp chỉ số nghiệm thu

| Tiêu chí | Mục tiêu cam kết (Mục 11) | Kết quả đạt được | Đánh giá |
|---|:---:|:---:|:---:|
| **Độ chính xác tìm kiếm (Retrieval Hit@5)** | **≥ 85.0%** | **100.0%** (21/21 câu) | ✅ ĐẠT |
| **Phân loại phạm vi (Scope Accuracy)** | **≥ 90.0%** | **100.0%** (25/25 câu) | ✅ ĐẠT |
| **Độ chính xác trích dẫn (Citation Validity)** | **≥ 90.0%** | **100.0%** (20 câu) | ✅ ĐẠT |
| **Trích dẫn ảo (Hallucination)** | **0%** | **0% (Không phát hiện)** | ✅ ĐẠT |

**KẾT LUẬN NGHIỆM THU:** 🎉 ĐẠT TIÊU CHUẨN NGHIỆM THU MVP

---

## 2. Chi tiết kết quả 25 câu hỏi kiểm thử

| ID | Nhóm | Câu hỏi | Điều kỳ vọng | Scope kỳ vọng | Scope thực tế | Retrieval | Trích dẫn | Độ trễ (ms) |
|---|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| TC-01 | keyword | Điều 1 Luật Trật tự an toàn giao thông đường bộ quy định về những gì? | Điều 1 | answered | ✅ answered | ✅ | ✅ | 2676.0 |
| TC-02 | keyword | Điều 10 quy định về quy tắc chung khi tham gia giao thông đường bộ như thế nào? | Điều 10 | answered | ✅ answered | ✅ | ✅ | 1720.4 |
| TC-03 | keyword | Điều 30 quy định về người đi bộ tham gia giao thông đường bộ như thế nào? | Điều 30 | answered | ✅ answered | ✅ | ✅ | 1999.7 |
| TC-04 | keyword | Điều 25 quy định về quy tắc giao thông trên đường cao tốc ra sao? | Điều 25 | answered | ✅ answered | ✅ | ✅ | 2068.1 |
| TC-05 | keyword | Điều 58 quy định gì về điểm của giấy phép lái xe? | Điều 58 | answered | ✅ answered | ✅ | ✅ | 1975.9 |
| TC-06 | keyword | Điều 88 quy định về hiệu lực thi hành của Luật này là khi nào? | Điều 88 | answered | ✅ answered | ✅ | ✅ | 1979.3 |
| TC-07 | situational | Uống ít bia mà trong hơi thở vẫn có cồn thì có được lái xe không? | Điều 9 | answered | ✅ answered | ✅ | ✅ | 1937.1 |
| TC-08 | situational | Trẻ em ngồi ghế phụ phía trước ô tô thì cần đáp ứng điều kiện gì? | Điều 10 | answered | ✅ answered | ✅ | ✅ | 1811.9 |
| TC-09 | situational | Khi gặp xe cứu thương đang phát tín hiệu ưu tiên thì người lái xe phải làm gì? | Điều 27 | answered | ✅ answered | ✅ | ✅ | 1676.4 |
| TC-10 | situational | Xe mô tô hai bánh có được đi vào đường cao tốc không? | Điều 25 | answered | ✅ answered | ✅ | ✅ | 1709.9 |
| TC-11 | situational | Đang lái xe ô tô có được dùng tay sử dụng điện thoại di động không? | Điều 9 | answered | ✅ answered | ✅ | ✅ | 2005.9 |
| TC-12 | situational | Khi qua vòng xuyến người lái xe phải nhường đường như thế nào? | Điều 22 | answered | ✅ answered | ✅ | ✅ | 2817.1 |
| TC-13 | situational | Người lái xe mô tô, xe gắn máy có bắt buộc phải đội mũ bảo hiểm không? | Điều 33 | answered | ✅ answered | ✅ | ✅ | 1860.9 |
| TC-14 | situational | Gặp tai nạn giao thông trên đường thì người có mặt tại hiện trường có trách nhiệm gì? | Điều 80 | answered | ✅ answered | ✅ | ✅ | 1838.8 |
| TC-15 | conditional_crossref | Xe máy được chở mấy người và những trường hợp nào được chở tối đa 2 người? | Điều 33 | answered | ✅ answered | ✅ | ✅ | 1866.2 |
| TC-16 | conditional_crossref | Bằng lái xe hạng A1 theo luật mới 2024 được điều khiển những loại xe gì? | Điều 57 | answered | ✅ answered | ✅ | ✅ | 1774.6 |
| TC-17 | conditional_crossref | Bằng lái hạng B theo luật mới 2024 quy định cho người lái loại xe nào? | Điều 57 | answered | ✅ answered | ✅ | ✅ | 1950.6 |
| TC-18 | conditional_crossref | Giấy phép lái xe bị trừ hết điểm thì sau bao lâu và làm cách nào để được phục hồi 12 điểm? | Điều 58 | answered | ✅ answered | ✅ | ✅ | 1702.3 |
| TC-19 | conditional_crossref | Quy định chuyển tiếp đối với giấy phép lái xe đã cấp trước ngày Luật có hiệu lực như thế nào? | Điều 89 | answered | ✅ answered | ✅ | ✅ | 2110.2 |
| TC-20 | conditional_crossref | Cơ quan nào có trách nhiệm quản lý nhà nước về sức khỏe của người lái xe và nồng độ cồn nội sinh? | Điều 87 | answered | ✅ answered | ✅ | ✅ | 1798.5 |
| TC-21 | out_of_scope_insufficient | Vượt đèn đỏ bằng ô tô bị phạt bao nhiêu tiền? | Điều 11 | insufficient_data | ✅ insufficient_data | ✅ | ✅ | 2060.1 |
| TC-22 | out_of_scope_insufficient | Chạy quá tốc độ 20km/h trên đường cao tốc bị phạt mấy triệu tiền mặt? | - | insufficient_data | ✅ insufficient_data | ✅ | ✅ | 1933.0 |
| TC-23 | out_of_scope_insufficient | Thời gian thử việc tối đa theo Luật Lao động là bao nhiêu tháng? | - | out_of_scope | ✅ out_of_scope | ✅ | ✅ | 0.0 |
| TC-24 | out_of_scope_insufficient | Biểu thuế lũy tiến từng phần thuế thu nhập cá nhân năm 2026 quy định như thế nào? | - | out_of_scope | ✅ out_of_scope | ✅ | ✅ | 0.0 |
| TC-25 | out_of_scope_insufficient | Hãy viết giúp tôi một bài thơ ngắn về mùa thu. | - | out_of_scope | ✅ out_of_scope | ✅ | ✅ | 0.0 |
