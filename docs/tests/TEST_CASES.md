# Danh sách Tổng hợp Test Cases (Test Cases Master List)

Dưới đây là bảng tổng hợp toàn bộ các Test Cases cho 5 tính năng cốt lõi của Autonomous AI Assistant (AAA). Vui lòng tham khảo các file `FEATURE_*.md` tương ứng để xem chi tiết các bước kiểm thử.

| Seq | Test Case ID | Test Case Name | Feature | Priority | Description |
| --- | ------------ | -------------- | ------- | -------- | ----------- |
| 1 | TC-NLP-001 | Trò chuyện thông thường (Chat cơ bản) | NLP Chat | Critical | Kiểm tra luồng chat cơ bản khi người dùng hỏi/đáp hội thoại thông thường. |
| 2 | TC-NLP-002 | Tự động gọi Plugin tạo sự kiện lịch | NLP Chat | Critical | Kiểm tra khả năng Agent phân tích ý định và tự động gọi tool `create_calendar_event`. |
| 3 | TC-NLP-003 | LLM trả về cấu trúc JSON bị lỗi (Negative) | NLP Chat | High | Kiểm tra cách hệ thống (ReAct Agent) xử lý khi LLM sinh ra output không đúng format JSON. |
| 4 | TC-NLP-004 | Plugin báo lỗi thực thi (Negative) | NLP Chat | High | Kiểm tra cách ToolExecutor phản hồi lại cho LLM khi một Tool quăng exception. |
| 5 | TC-EML-001 | Cảnh báo Email VIP (Positive) | Email Alerts | Critical | Quét thấy email từ VIP list và đẩy Toast Alert lên giao diện ngay lập tức. |
| 6 | TC-EML-002 | Cảnh báo Email Khẩn cấp có Keyword (Positive) | Email Alerts | High | Quét thấy email bình thường nhưng tiêu đề chứa chữ "URGENT", kích hoạt cảnh báo. |
| 7 | TC-EML-003 | Cảnh báo trùng lặp (Boundary/Negative) | Email Alerts | Medium | Kiểm tra tính năng Deduplication của AlertEngine khi worker quét cùng 1 email khẩn nhiều lần. |
| 8 | TC-CAL-001 | Nhắc nhở sự kiện diễn ra trong 5 phút tới (Positive) | In-app Calendar | Critical | Hệ thống tự động bắn cảnh báo (Toast) khi có sự kiện sẽ diễn ra trong vòng < 5 phút. |
| 9 | TC-CAL-002 | Bỏ qua sự kiện đã quá hạn (Negative) | In-app Calendar | Medium | Hệ thống không cảnh báo các sự kiện đã diễn ra trong quá khứ hoặc đã có cờ `is_notified=True`. |
| 10 | TC-CAL-003 | Ranh giới thời gian đúng 5 phút 00 giây (Boundary) | In-app Calendar | High | Kiểm thử vùng cận ranh giới của điều kiện cảnh báo thời gian. |
| 11 | TC-HYB-001 | Tự động Fallback từ OpenAI sang Ollama khi rớt mạng (Positive) | Hybrid LLM | Critical | Giả lập tắt mạng để API OpenAI bị timeout, kiểm tra xem LLM Factory có tự rẽ sang Local Model không. |
| 12 | TC-HYB-002 | Cả Cloud và Local đều chết (Negative) | Hybrid LLM | High | Tắt mạng và tắt cả Ollama, kiểm tra hệ thống có trả về thông báo lỗi thân thiện thay vì crash không. |

| 15 | TC-SET-001 | Tắt quyền truy cập Mạng của Email Plugin | Settings | High | Vô hiệu hóa permission `network` của EmailPlugin và gọi tool, kỳ vọng báo lỗi Authorization. |
| 16 | TC-SET-002 | Cập nhật API Key mới cho OpenAI | Settings | Medium | Lưu API key bị sai và kiểm tra kết nối có bị từ chối không, sau đó sửa lại key đúng. |
