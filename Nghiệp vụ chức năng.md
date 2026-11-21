# NGHIỆP VỤ CHỨC NĂNG

## Hệ thống trợ lý tra cứu pháp luật Việt Nam

**Mã dự án:** VN-Legal RAG Assistant  
**Phiên bản:** 1.1  
**Phạm vi:** MVP giai đoạn 1  
**Trạng thái:** Bản nháp để thống nhất nghiệp vụ  
**Ngày cập nhật:** 21/11/2026

---

## 1. Mục đích tài liệu

Tài liệu này mô tả mục tiêu, phạm vi, hành vi và tiêu chí nghiệm thu của hệ thống trợ lý tra cứu pháp luật Việt Nam.

Tài liệu tập trung vào yêu cầu nghiệp vụ và kết quả người dùng nhận được. Các lựa chọn công nghệ như mô hình ngôn ngữ, thư viện tìm kiếm, cơ sở dữ liệu vector hoặc nền tảng triển khai sẽ được quyết định trong tài liệu thiết kế kỹ thuật riêng.

## 2. Bối cảnh và vấn đề cần giải quyết

Văn bản pháp luật có cấu trúc nhiều tầng gồm Chương, Điều, Khoản và Điểm. Người dùng thường biết tình huống thực tế nhưng không biết từ khóa pháp lý hoặc số Điều cần tìm.

Hệ thống hỏi đáp dựa trên mô hình ngôn ngữ có thể trả lời trôi chảy nhưng nhầm văn bản, nhầm quy định đã hết hiệu lực hoặc tự tạo ra Điều luật không tồn tại. Vì vậy hệ thống cần trả lời dựa trên nguồn pháp luật đã được nạp, hiển thị nguồn để người dùng kiểm tra và thông báo rõ khi dữ liệu hiện tại không đủ.

## 3. Mục tiêu sản phẩm

Hệ thống MVP cần đạt các mục tiêu sau:

1. Cho phép người dùng hỏi bằng tiếng Việt tự nhiên về một văn bản pháp luật cụ thể.
2. Tìm được Điều, Khoản hoặc Điểm liên quan dù người dùng hỏi bằng từ khóa pháp lý hoặc cách diễn đạt đời thường.
3. Trả lời dựa trên nội dung đã truy xuất từ văn bản nguồn.
4. Hiển thị trích dẫn để người dùng kiểm tra căn cứ của câu trả lời.
5. Nhận biết câu hỏi ngoài phạm vi hoặc yêu cầu thông tin chưa có trong dữ liệu.
6. Hỗ trợ các câu hỏi có tham chiếu đến Điều hoặc Khoản khác.
7. Có bộ câu hỏi đánh giá để đo chất lượng tìm kiếm, trích dẫn và từ chối.

Hệ thống là công cụ hỗ trợ tra cứu, không thay thế luật sư, cơ quan nhà nước hoặc tư vấn pháp lý chính thức.

## 4. Đối tượng sử dụng

### 4.1. Người dùng tra cứu

Người dân, tài xế, nhân viên hành chính hoặc người cần tìm hiểu nhanh các quy định về trật tự, an toàn giao thông đường bộ.

Người dùng có thể không biết số Điều và có thể đặt câu hỏi bằng tình huống đời thường.

### 4.2. Người đánh giá sản phẩm

Người đánh giá cần kiểm tra được:

- hệ thống đang sử dụng văn bản nào;
- câu trả lời dựa trên Điều, Khoản nào;
- hệ thống xử lý câu hỏi ngoài phạm vi ra sao;
- chất lượng tìm kiếm và trích dẫn được đo như thế nào.

## 5. Phạm vi MVP

### 5.1. Văn bản được hỗ trợ

MVP sử dụng văn bản do người quản trị cung cấp:

- **Tên:** Luật Trật tự, an toàn giao thông đường bộ;
- **Số hiệu:** 36/2024/QH15;
- **Ngày ban hành:** 27/06/2024;
- **Ngày có hiệu lực chung:** 01/01/2025;
- **Phạm vi dữ liệu dự kiến:** 9 Chương, 89 Điều.

Thông tin hiệu lực và nội dung pháp lý phải được đối chiếu với nguồn chính thức trước khi sử dụng cho mục đích thực tế. File `luat_giao_thong_2024_clean.docx` là dữ liệu đầu vào của bản MVP.

### 5.2. Nội dung có thể tra cứu

Hệ thống hỗ trợ tra cứu các nội dung xuất hiện trong văn bản đã nạp, gồm:

- quy tắc giao thông đường bộ;
- hành vi bị nghiêm cấm;
- phương tiện tham gia giao thông;
- giấy phép lái xe và điều kiện điều khiển phương tiện;
- điểm của giấy phép lái xe;
- tuần tra, kiểm soát và chỉ huy giao thông;
- giải quyết tai nạn giao thông;
- quản lý nhà nước;
- hiệu lực và quy định chuyển tiếp.

### 5.3. Nội dung ngoài phạm vi

Trong MVP, hệ thống không có đủ căn cứ để trả lời đầy đủ các nhóm sau:

- mức tiền phạt hoặc mức trừ điểm cụ thể nếu thông tin đó nằm trong văn bản khác chưa được nạp;
- quy định về xây dựng, bảo trì hạ tầng đường bộ thuộc văn bản khác;
- Luật Lao động, Luật Dân sự, Luật Hình sự, pháp luật thuế, kế toán và các lĩnh vực chưa được nạp;
- tranh chấp hoặc hồ sơ pháp lý cá nhân cần đánh giá chuyên môn;
- kết luận thay cho cơ quan có thẩm quyền hoặc luật sư;
- thông tin pháp luật phát sinh sau phiên bản dữ liệu đang sử dụng nếu chưa được cập nhật.

Khi gặp câu hỏi ngoài phạm vi, hệ thống phải thông báo giới hạn dữ liệu thay vì tự sử dụng kiến thức nền để suy đoán.

## 6. Nguyên tắc nghiệp vụ

### 6.1. Nguyên tắc về nguồn

1. Mọi kết luận pháp lý phải dựa trên nội dung được truy xuất từ văn bản đã nạp.
2. Không được tự tạo số Điều, Khoản, Điểm hoặc nội dung không có trong nguồn.
3. Nếu các nguồn truy xuất được mâu thuẫn hoặc chưa đủ để kết luận, hệ thống phải nêu rõ điều đó.
4. Câu trả lời phải phân biệt nội dung có trong văn bản với phần hệ thống chưa có dữ liệu.
5. Tên văn bản, số hiệu và thông tin phiên bản phải được hiển thị nhất quán.

### 6.2. Nguyên tắc về trích dẫn

Mỗi ý pháp lý trong câu trả lời phải có ít nhất một trích dẫn phù hợp. Trích dẫn nên bao gồm:

- tên văn bản;
- Điều;
- Khoản nếu có;
- Điểm nếu có.

Ví dụ:

`[Luật Trật tự, an toàn giao thông đường bộ 36/2024/QH15, Điều 9, khoản 2]`

Hệ thống phải cho phép người dùng mở phần nguồn để xem nội dung nguyên văn của các đoạn đã được sử dụng.

### 6.3. Nguyên tắc về câu trả lời ngoài phạm vi

Hệ thống phân loại câu hỏi theo ba trạng thái:

1. **Có thể trả lời:** dữ liệu có căn cứ phù hợp.
2. **Đúng lĩnh vực nhưng thiếu dữ liệu:** có thể giải thích phần nằm trong văn bản hiện tại và nêu rõ phần còn thiếu.
3. **Ngoài lĩnh vực hỗ trợ:** từ chối ngắn gọn và thông báo phạm vi hiện tại.

Ví dụ với câu hỏi “Vượt đèn đỏ bằng ô tô bị phạt bao nhiêu tiền?”:

- hệ thống có thể giải thích quy định về việc chấp hành đèn tín hiệu nếu có trong văn bản;
- hệ thống phải nói rõ dữ liệu hiện tại chưa bao gồm căn cứ về mức tiền phạt cụ thể;
- hệ thống không được tự đưa ra một mức phạt nếu chưa có văn bản tương ứng.

## 7. Kịch bản sử dụng chính

### UC-01: Tra cứu theo số Điều

**Tác nhân:** Người dùng  
**Mục tiêu:** Tìm nội dung của một Điều cụ thể.

**Luồng chính:**

1. Người dùng nhập câu hỏi có số Điều, ví dụ: “Điều 58 quy định gì về điểm giấy phép lái xe?”
2. Hệ thống nhận diện số Điều và các từ khóa liên quan.
3. Hệ thống tìm Điều và Khoản phù hợp.
4. Hệ thống trả lời bằng ngôn ngữ dễ hiểu.
5. Hệ thống hiển thị trích dẫn và nội dung nguồn.

### UC-02: Tra cứu theo từ khóa pháp lý

**Tác nhân:** Người dùng  
**Mục tiêu:** Tìm quy định bằng thuật ngữ hoặc cụm từ chính xác.

Ví dụ:

- “nồng độ cồn”;
- “vòng xuyến”;
- “hạng B1”;
- “điểm giấy phép lái xe”.

Hệ thống cần ưu tiên các kết quả chứa đúng từ khóa, đồng thời kết hợp với các đoạn có ý nghĩa tương đương.

### UC-03: Hỏi bằng tình huống đời thường

**Tác nhân:** Người dùng  
**Mục tiêu:** Hỏi quy định bằng cách diễn đạt không mang tính pháp lý.

Ví dụ:

> “Uống một ít bia nhưng máy đo vẫn có cồn thì có được chạy xe không?”

Hệ thống phải tìm được quy định phù hợp và giải thích ngắn gọn, có trích dẫn.

### UC-04: Hỏi về Điều có tham chiếu chéo

**Tác nhân:** Người dùng  
**Mục tiêu:** Nhận được câu trả lời đầy đủ khi một Điều dẫn chiếu sang Điều hoặc Khoản khác.

**Yêu cầu:**

1. Nhận diện tham chiếu như “theo Điều 59” hoặc “quy định tại khoản 2 Điều này”.
2. Tìm thêm phần được dẫn chiếu khi cần.
3. Đưa nguồn chính và nguồn tham chiếu vào câu trả lời.
4. Hiển thị rõ nguồn nào là căn cứ chính, nguồn nào là căn cứ bổ sung.

### UC-05: Hỏi nối tiếp trong cùng cuộc trò chuyện

**Tác nhân:** Người dùng  
**Trạng thái:** Có thể triển khai sau khi MVP lõi ổn định.

Ví dụ:

1. Người dùng hỏi: “Xe máy được chở mấy người?”
2. Người dùng hỏi tiếp: “Nếu là trẻ em thì sao?”

Nếu bật tính năng hội thoại, hệ thống phải hiểu câu hỏi thứ hai dựa trên ngữ cảnh gần nhất. Nếu không đủ ngữ cảnh, hệ thống phải yêu cầu người dùng nói rõ hơn thay vì tự đoán.

### UC-06: Hỏi ngoài phạm vi

**Tác nhân:** Người dùng  
**Mục tiêu:** Nhận được thông báo rõ ràng khi câu hỏi không thuộc dữ liệu hiện tại.

Ví dụ:

> “Thời gian thử việc tối đa theo Luật Lao động là bao lâu?”

Kết quả mong đợi:

> “Tài liệu hiện tại chỉ hỗ trợ tra cứu Luật Trật tự, an toàn giao thông đường bộ và chưa có dữ liệu về Luật Lao động.”

### UC-07: Hỏi thông tin chưa có trong văn bản

**Tác nhân:** Người dùng  
**Mục tiêu:** Phân biệt câu hỏi đúng lĩnh vực nhưng cần văn bản bổ sung.

Ví dụ:

> “Vượt đèn đỏ bị phạt bao nhiêu tiền?”

Hệ thống phải nêu phần quy định có thể tìm thấy trong văn bản hiện tại và thông báo rằng dữ liệu chưa có văn bản quy định mức phạt cụ thể.

## 8. Yêu cầu chức năng

### FR-01. Quản lý và kiểm tra dữ liệu pháp luật

Hệ thống phải:

1. Đọc được file văn bản đầu vào theo định dạng được thống nhất.
2. Giữ được thứ tự Chương, Điều, Khoản và Điểm.
3. Làm sạch khoảng trắng dư thừa và ký tự điều khiển mà không làm mất nội dung pháp lý.
4. Không làm mất các ký hiệu như `<`, `>`, `≤`, `≥`, số thập phân và đơn vị đo.
5. Kiểm tra số lượng Điều dự kiến của văn bản.
6. Cảnh báo khi có Điều bị thiếu, trùng, rỗng hoặc sai thứ tự.
7. Lưu được bản dữ liệu đã xử lý để kiểm tra lại.

### FR-02. Phân đoạn và gắn cấu trúc

Hệ thống phải:

1. Ưu tiên giữ trọn một Điều trong một đơn vị tìm kiếm khi độ dài cho phép.
2. Tách Điều dài theo Khoản hoặc nhóm Khoản, không cắt giữa câu hoặc giữa nội dung pháp lý.
3. Lặp lại tiêu đề Chương và Điều trong mỗi đoạn con để giữ ngữ cảnh.
4. Cho phép truy ngược mỗi đoạn tìm kiếm về Điều, Khoản và Điểm trong văn bản gốc.
5. Gom các đoạn thuộc cùng một Điều khi hiển thị nguồn.

Mỗi đoạn cần có tối thiểu các trường:

```json
{
  "id": "giao_thong_36_2024_dieu_58_khoan_1",
  "document_id": "luat_trat_tu_an_toan_giao_thong_36_2024",
  "law_number": "36/2024/QH15",
  "law_name": "Luật Trật tự, an toàn giao thông đường bộ",
  "chapter_number": 4,
  "chapter_title": "Người điều khiển phương tiện tham gia giao thông đường bộ",
  "article_number": 58,
  "article_title": "Điểm của giấy phép lái xe",
  "clause_number": 1,
  "point": null,
  "text": "...",
  "references": []
}
```

### FR-03. Tìm kiếm nội dung

Hệ thống phải:

1. Nhận câu hỏi tiếng Việt tự nhiên.
2. Tìm được kết quả theo số Điều, Khoản, Điểm và từ khóa chính xác.
3. Tìm được kết quả theo ý nghĩa gần với câu hỏi.
4. Kết hợp kết quả tìm kiếm từ khóa và kết quả tìm kiếm ngữ nghĩa.
5. Cho phép giới hạn phạm vi theo văn bản hoặc lĩnh vực khi hệ thống mở rộng.
6. Loại bỏ hoặc gom các kết quả trùng nội dung.
7. Trả về điểm và thông tin nguồn để phục vụ kiểm tra, nhưng không dùng điểm kỹ thuật thay cho kết luận pháp lý.

Việc quyết định câu hỏi có đủ căn cứ để trả lời phải dựa trên nhiều tín hiệu, gồm kết quả tìm kiếm, phạm vi câu hỏi và bộ quy tắc nghiệp vụ. Không được dùng một ngưỡng điểm cố định chưa được kiểm chứng làm căn cứ duy nhất.

### FR-04. Sinh câu trả lời

Hệ thống phải:

1. Chỉ sử dụng các nguồn đã được truy xuất để tạo câu trả lời pháp lý.
2. Trả lời bằng tiếng Việt, ngắn gọn và dễ hiểu.
3. Phân biệt rõ nội dung luật và phần giải thích diễn đạt lại.
4. Nêu điều kiện, ngoại lệ hoặc thời điểm hiệu lực khi các thông tin đó liên quan đến câu hỏi.
5. Gắn trích dẫn cho từng ý pháp lý.
6. Không khẳng định vượt quá nội dung nguồn.
7. Nêu rõ khi chưa đủ căn cứ để kết luận.
8. Không tự đưa ra mức phạt, thời hạn hoặc điều kiện không xuất hiện trong nguồn được sử dụng.

### FR-05. Xử lý tham chiếu chéo

Hệ thống phải:

1. Nhận diện các tham chiếu đến Điều, Khoản hoặc Điểm khác.
2. Tìm thêm nội dung được dẫn chiếu trong phạm vi văn bản.
3. Giới hạn số lượng nội dung bổ sung để tránh đưa ngữ cảnh không liên quan vào câu trả lời.
4. Gắn trích dẫn riêng cho nội dung từ nguồn bổ sung.
5. Thông báo khi tham chiếu dẫn đến văn bản chưa được nạp.

### FR-06. Từ chối và cảnh báo

Hệ thống phải từ chối hoặc cảnh báo trong các trường hợp:

1. Câu hỏi rỗng.
2. Câu hỏi vượt quá giới hạn độ dài được cấu hình.
3. Câu hỏi ngoài lĩnh vực hoặc văn bản hỗ trợ.
4. Không tìm thấy nguồn đủ liên quan.
5. Câu hỏi cần văn bản chưa được nạp.
6. Dữ liệu nguồn có lỗi hoặc không xác định được vị trí trích dẫn.
7. Dịch vụ mô hình hoặc dịch vụ tìm kiếm tạm thời không hoạt động.

Thông báo phải dễ hiểu, không hiển thị lỗi kỹ thuật hoặc thông tin bí mật.

### FR-07. Giao diện tra cứu

Giao diện MVP cần có:

- tên hệ thống và phạm vi văn bản đang hỗ trợ;
- ô nhập câu hỏi;
- khu vực hiển thị lịch sử câu hỏi và câu trả lời;
- trích dẫn mở rộng được;
- nội dung nguồn đã truy xuất;
- thông tin phiên bản văn bản;
- nút xóa lịch sử;
- một số câu hỏi mẫu;
- thông báo rõ khi câu hỏi ngoài phạm vi hoặc hệ thống chưa đủ dữ liệu.

Các thông số kỹ thuật như điểm tìm kiếm hoặc thời gian phản hồi có thể hiển thị ở chế độ đánh giá, nhưng không được làm người dùng hiểu nhầm đó là mức độ chính xác pháp lý.

### FR-08. Đánh giá chất lượng

Hệ thống phải có bộ dữ liệu đánh giá tối thiểu 25 câu hỏi, chia thành:

1. Tra cứu trực tiếp theo Điều hoặc từ khóa: 6 câu.
2. Tình huống đời thường: 8 câu.
3. Câu hỏi có điều kiện, ngoại lệ hoặc tham chiếu chéo: 6 câu.
4. Câu hỏi ngoài phạm vi hoặc thiếu văn bản: 5 câu.

Mỗi câu hỏi cần ghi:

- nội dung câu hỏi;
- nhóm câu hỏi;
- Điều/Khoản/Điểm kỳ vọng;
- trạng thái kỳ vọng: trả lời, cảnh báo hoặc từ chối;
- các ý chính bắt buộc;
- nguồn dùng để chấm.

## 9. Yêu cầu về giao diện và trải nghiệm

Giao diện cần giúp người dùng trả lời được ba câu hỏi:

1. Hệ thống đang dựa vào văn bản nào?
2. Câu trả lời được căn cứ vào phần nào?
3. Hệ thống có đang thiếu dữ liệu để kết luận không?

Câu trả lời nên được trình bày theo thứ tự:

1. Kết luận ngắn.
2. Giải thích hoặc điều kiện liên quan.
3. Trích dẫn.
4. Ghi chú giới hạn dữ liệu nếu có.

## 10. Yêu cầu phi chức năng

### 10.1. Tính chính xác và kiểm chứng

- Không mất nội dung khi xử lý văn bản.
- Mỗi nguồn hiển thị phải truy ngược được về vị trí trong văn bản.
- Câu trả lời pháp lý phải có căn cứ.
- Các lỗi phát hiện trong dữ liệu phải được ghi nhận để sửa trước khi đánh giá.

### 10.2. Hiệu năng

Trong môi trường demo với một văn bản và số lượng người dùng thấp:

- thời gian tìm kiếm nội bộ nên dưới 1 giây;
- thời gian phản hồi toàn bộ nên hướng tới dưới 6 giây khi dịch vụ ngoài hoạt động bình thường;
- thời gian đo phải tách riêng thời gian tìm kiếm và thời gian sinh câu trả lời.

Đây là mục tiêu cho môi trường demo, không phải cam kết cho mọi môi trường triển khai.

### 10.3. Khả năng chịu lỗi

Hệ thống không được hiển thị traceback cho người dùng. Khi dịch vụ ngoài lỗi hoặc hết hạn mức, hệ thống phải hiển thị thông báo thân thiện và ghi log đủ để kiểm tra.

### 10.4. Bảo mật

- Không ghi API key vào mã nguồn hoặc dữ liệu đánh giá.
- Không đưa thông tin bí mật vào câu trả lời.
- Không lưu câu hỏi và lịch sử hội thoại lâu hơn thời gian cần thiết nếu chưa có quy định lưu trữ.
- Cấu hình bí mật phải được quản lý bằng biến môi trường hoặc cơ chế bí mật của môi trường triển khai.

### 10.5. Khả năng mở rộng

Mô hình dữ liệu cần cho phép bổ sung văn bản khác trong tương lai. Việc mở rộng không được làm thay đổi cấu trúc căn bản của dữ liệu hiện tại.

Việc hỗ trợ thêm lĩnh vực luật, cập nhật văn bản, quản lý người dùng hoặc cung cấp API riêng không thuộc MVP này.

## 11. Tiêu chí nghiệm thu MVP

### 11.1. Dữ liệu

- Tách đủ 89 Điều theo dữ liệu đầu vào dự kiến.
- Không có đoạn rỗng ngoài các phần rỗng hợp lệ của văn bản.
- Không mất số, ký hiệu, đơn vị hoặc dấu câu quan trọng.
- Mỗi đoạn tra cứu truy ngược được về Chương, Điều và vị trí tương ứng.

### 11.2. Tìm kiếm

- Ít nhất 85% câu hỏi trong bộ đánh giá có Điều kỳ vọng xuất hiện trong nhóm kết quả đầu tiên được cấu hình.
- Kết quả tìm kiếm theo số Điều và từ khóa chính xác phải được ưu tiên.
- Các câu hỏi diễn đạt đời thường phải tìm được nguồn phù hợp trong các câu kiểm thử đã chuẩn bị.

### 11.3. Câu trả lời và trích dẫn

- Ít nhất 90% câu trả lời có trích dẫn đúng đến Điều.
- Với các test yêu cầu Khoản hoặc Điểm, trích dẫn phải đúng đến cấp đó.
- Câu trả lời không được đưa thêm mức phạt hoặc thông tin ngoài nguồn.
- Câu hỏi có tham chiếu chéo phải có cả nguồn chính và nguồn được dẫn chiếu khi cần.

### 11.4. Từ chối và giới hạn dữ liệu

- Ít nhất 95% câu hỏi ngoài phạm vi trong bộ đánh giá được từ chối hoặc cảnh báo đúng.
- Các câu hỏi về mức phạt khi chưa có văn bản xử phạt phải được thông báo thiếu dữ liệu.
- Hệ thống không được bịa Điều, Khoản, Điểm hoặc mức phạt trong các câu hỏi gài bẫy.

### 11.5. Giao diện và lỗi

- Người dùng xem được văn bản và phiên bản dữ liệu đang dùng.
- Người dùng mở được nguồn trích dẫn.
- Có thể xóa lịch sử tra cứu.
- Lỗi mạng hoặc lỗi dịch vụ không làm giao diện bị văng lỗi kỹ thuật.

## 12. Bộ câu hỏi kiểm thử ban đầu

| ID | Nhóm | Câu hỏi | Kết quả kỳ vọng |
|---|---|---|---|
| TC-01 | Từ khóa | Uống ít bia mà trong hơi thở vẫn có cồn thì có được lái xe không? | Trả lời dựa trên quy định về nồng độ cồn, có trích dẫn đúng Điều/Khoản. |
| TC-02 | Tình huống | Trẻ em ngồi ghế phụ phía trước ô tô cần đáp ứng điều kiện gì? | Nêu đúng điều kiện và thời điểm áp dụng nếu có trong nguồn. |
| TC-03 | Ngoại lệ | Xe máy được chở mấy người và trường hợp nào được chở thêm người? | Nêu quy tắc chung và các trường hợp ngoại lệ, có trích dẫn. |
| TC-04 | Chuyên môn | Bằng lái hạng A1 được điều khiển loại xe nào? | Trả lời đúng giới hạn trong văn bản, giữ nguyên số và đơn vị. |
| TC-05 | Cơ chế mới | Giấy phép lái xe có bao nhiêu điểm và khi bị trừ hết điểm thì xử lý thế nào? | Tóm tắt đủ các điều kiện liên quan, có trích dẫn. |
| TC-06 | Tham chiếu chéo | Điều kiện điều khiển xe gắn máy có dẫn chiếu sang Điều nào khác không? | Hiển thị nguồn chính và Điều được dẫn chiếu nếu có. |
| TC-07 | Thiếu dữ liệu | Vượt đèn đỏ bằng ô tô bị phạt bao nhiêu tiền? | Nêu quy định có thể tìm trong luật và thông báo chưa có dữ liệu mức phạt cụ thể. |
| TC-08 | Ngoài phạm vi | Thử việc tối đa bao nhiêu ngày theo Luật Lao động? | Từ chối vì chưa hỗ trợ Luật Lao động. |
| TC-09 | Ngoài phạm vi | Cách tính thuế thu nhập cá nhân năm 2026 như thế nào? | Từ chối vì chưa hỗ trợ pháp luật thuế. |
| TC-10 | Ngoài phạm vi | Viết giúp tôi một chương trình Python. | Từ chối vì không thuộc chức năng tra cứu pháp luật. |

## 13. Dữ liệu đầu vào và quản lý phiên bản

Mỗi lần nạp văn bản cần lưu được:

- tên file nguồn;
- tên và số hiệu văn bản;
- ngày ban hành;
- ngày hiệu lực;
- thời điểm nạp dữ liệu;
- phiên bản dữ liệu;
- nguồn phát hành hoặc đường dẫn chính thức nếu có;
- trạng thái kiểm tra dữ liệu;
- danh sách lỗi hoặc cảnh báo.

Khi văn bản được sửa đổi hoặc thay thế, hệ thống phải phân biệt được phiên bản cũ và phiên bản mới. Không được trộn nội dung của các phiên bản nếu chưa có quy tắc xác định hiệu lực.

## 14. Những nội dung chưa thuộc MVP

Các nội dung sau được để dành cho giai đoạn sau:

- nạp và quản lý nhiều bộ luật qua giao diện quản trị;
- tự động theo dõi văn bản mới ban hành;
- xử lý toàn bộ nghị định, thông tư và văn bản hướng dẫn;
- tư vấn pháp lý cá nhân hóa;
- phân tích hồ sơ hoặc dự đoán kết quả tranh chấp;
- tài khoản người dùng và phân quyền;
- triển khai API công khai;
- đánh giá tự động bằng mô hình giám khảo;
- hỗ trợ đa ngôn ngữ.

## 15. Điều kiện chuyển sang bước thiết kế kỹ thuật

Chỉ chuyển sang thiết kế và lập trình sau khi thống nhất:

1. văn bản nguồn và phạm vi dữ liệu;
2. cấu trúc Điều, Khoản, Điểm;
3. quy tắc trả lời và trích dẫn;
4. quy tắc từ chối và cảnh báo thiếu dữ liệu;
5. bộ câu hỏi kiểm thử;
6. tiêu chí nghiệm thu.

