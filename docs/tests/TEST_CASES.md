# Danh sách Tổng hợp Test Cases (Test Cases Master List)

Dưới đây là bảng tổng hợp toàn bộ các Test Cases cho 5 tính năng cốt lõi của Autonomous AI Assistant (AAA). Vui lòng tham khảo các file `FEATURE_*.md` tương ứng để xem chi tiết các bước kiểm thử.

| Seq | Test Case ID | Test Case Name | Feature | Priority | Description |
| --- | ------------ | -------------- | ------- | -------- | ----------- |
| 1 | TC-NLP-001 | Trò chuyện thông thường (Chat cơ bản) | NLP Chat | Critical | Kiểm tra luồng chat cơ bản khi người dùng hỏi/đáp hội thoại thông thường. |
| 2 | TC-NLP-002 | Tự động gọi Plugin tạo sự kiện lịch | NLP Chat | Critical | Kiểm tra khả năng Agent phân tích ý định và tự động gọi tool `create_calendar_event`. |
| 3 | TC-NLP-003 | LLM trả về cấu trúc JSON bị lỗi (Negative) | NLP Chat | High | Kiểm tra cách hệ thống (ReAct Agent) xử lý khi LLM sinh ra output không đúng format JSON. |
| 4 | TC-NLP-004 | Plugin báo lỗi thực thi (Negative) | NLP Chat | High | Kiểm tra cách ToolExecutor phản hồi lại cho LLM khi một Tool quăng exception. |
| 5 | TC-NLP-005 | Câu lệnh Chat cực dài | NLP Chat | Medium | Gửi nội dung tin nhắn vượt quá giới hạn Token thông thường (Boundary). |
| 6 | TC-NLP-006 | Hủy tiến trình AI (True Full Kill / Stop) | NLP Chat | High | Xác thực khả năng gián đoạn hoàn toàn luồng sinh text của LLM tại Backend. |
| 7 | TC-NLP-007 | Nhập liệu bằng giọng nói (Voice Input) | NLP Chat | Medium | Kiểm tra chức năng chuyển đổi giọng nói thành văn bản bằng Web Speech API. |
| 8 | TC-NLP-008 | Thư viện Mẫu lệnh (Prompt Library) | NLP Chat | Low | Kiểm tra tính năng chọn nhanh các kịch bản có sẵn. |
| 9 | TC-NLP-009 | Ghi nhớ thông tin cá nhân (Memory Plugin) | NLP Chat | Critical | Kiểm tra khả năng lưu trữ thông tin cá nhân vào trí nhớ dài hạn. |
| 10 | TC-NLP-010 | Quản lý công việc (Task Plugin) | NLP Chat | High | Kiểm tra khả năng tạo công việc và gọi tool liên tiếp (Chain of Thought). |
| 11 | TC-NLP-011 | Tra cứu Web (Web Search Plugin) | NLP Chat | Medium | Kiểm tra khả năng kết nối mạng để tìm kiếm thông tin theo thời gian thực. |
| 12 | TC-NLP-012 | Thiếu tham số (Missing Arguments Edge Case) | NLP Chat | High | Kiểm tra khả năng bắt lỗi thiếu thông tin, AI KHÔNG được bịa đặt tham số. |
| 13 | TC-EML-001 | Cảnh báo Email VIP (Positive) | Email Alerts | Critical | Quét thấy email từ VIP list và đẩy Toast Alert lên giao diện ngay lập tức. |
| 14 | TC-EML-002 | Cảnh báo Email Khẩn cấp có Keyword (Positive) | Email Alerts | High | Quét thấy email bình thường nhưng tiêu đề chứa chữ "URGENT", kích hoạt cảnh báo. |
| 15 | TC-EML-003 | Cảnh báo trùng lặp (Boundary/Negative) | Email Alerts | Medium | Kiểm tra tính năng Deduplication của AlertEngine khi worker quét cùng 1 email khẩn nhiều lần. |
| 16 | TC-CAL-001 | Nhắc nhở sự kiện diễn ra trong 5 phút tới (Positive) | In-app Calendar | Critical | Hệ thống tự động bắn cảnh báo (Toast) khi có sự kiện sẽ diễn ra trong vòng < 5 phút. |
| 17 | TC-CAL-002 | Bỏ qua sự kiện đã quá hạn (Negative) | In-app Calendar | Medium | Hệ thống không cảnh báo các sự kiện đã diễn ra trong quá khứ hoặc đã có cờ `is_notified=True`. |
| 18 | TC-CAL-003 | Ranh giới thời gian đúng 5 phút 00 giây (Boundary) | In-app Calendar | High | Kiểm thử vùng cận ranh giới của điều kiện cảnh báo thời gian. |
| 19 | TC-HYB-001 | Tự động Fallback từ OpenAI sang Ollama khi rớt mạng (Positive) | Hybrid LLM | Critical | Giả lập tắt mạng để API OpenAI bị timeout, kiểm tra xem LLM Factory có tự rẽ sang Local Model không. |
| 20 | TC-HYB-002 | Cả Cloud và Local đều chết (Negative) | Hybrid LLM | High | Tắt mạng và tắt cả Ollama, kiểm tra hệ thống có trả về thông báo lỗi thân thiện thay vì crash không. |
| 21 | TC-SET-001 | Tắt quyền truy cập Mạng của Email Plugin | Settings | High | Vô hiệu hóa permission `network` của EmailPlugin và gọi tool, kỳ vọng báo lỗi Authorization. |
| 22 | TC-SET-002 | Cập nhật API Key mới cho OpenAI | Settings | Medium | Lưu API key bị sai và kiểm tra kết nối có bị từ chối không, sau đó sửa lại key đúng. |
