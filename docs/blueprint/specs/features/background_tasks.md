# Đặc tả Nghiệp vụ Xử lý Nền & Trích xuất Dữ liệu (Background Tasks Specs)

Tài liệu này quy định các nguyên tắc thiết kế và luồng nghiệp vụ của các tiến trình chạy ngầm (Workers/Cron Jobs) trong dự án AAA. Hệ thống Background Tasks chịu trách nhiệm kết nối với thế giới bên ngoài (Email, Lịch, Trình duyệt) một cách âm thầm, cung cấp nguồn dữ liệu sạch cho Lõi AI phân tích mà không làm gián đoạn trải nghiệm Chat (Non-blocking).

---

## 1. User Stories (Câu Chuyện Người Dùng)

- **US01 (Kiểm tra dữ liệu ngầm)**: *Là một người làm việc cường độ cao*, tôi muốn Trợ lý AI tự động quét email và lịch họp mới mỗi 15 phút ở chế độ nền, *để* tôi luôn được cập nhật những thông tin thay đổi đột xuất (như dời lịch họp) mà không cần phải ra lệnh thủ công. Đồng thời, tôi muốn ứng dụng tự động bóc tách các mốc thời gian trong email và đồng bộ vào lịch/deadline công việc thay vì tôi phải tự thao tác tay (Autonomous Sync).
- **US02 (Nhắc nhở công việc)**: *Là một người dùng Desktop*, tôi muốn nhận được thông báo Native OS Notification mỗi khi có Lịch họp sắp diễn ra hoặc Công việc (Task) sắp đến hạn, *để* không bị lỡ kế hoạch.
- **US03 (Mượt mà không treo máy)**: *Là một người dùng Desktop*, tôi muốn quá trình tải file hoặc cào dữ liệu hàng loạt không làm khựng hay treo giao diện chat, *để* tôi vẫn có thể trao đổi mượt mà với AI về các chủ đề khác trong lúc đợi dữ liệu về.
- **US04 (Xử lý Ngoại tuyến - Offline Resiliency)**: *Là một người hay di chuyển*, tôi muốn hệ thống tự động ghi nhận lại các tác vụ đang làm dở khi bị mất Wifi (vd: rớt mạng giữa lúc đang tóm tắt trang web), và tự động thử lại khi có mạng, *để* tôi không phải ra lệnh lại từ đầu.

---

## 2. Luồng Thực Thi Chạy Ngầm (Background Execution Flows)

Mọi tiến trình nền đều tuân thủ nguyên tắc **Bất đồng bộ (Asynchronous)** (Dùng `async/await` của Python) và **Tách rời (Decoupled)** thông qua kiến trúc Plugin và Event Bus.

### Luồng Hoạt Động Của Một Worker Tiêu Biểu (Ví dụ: EmailSyncWorker)
1. **Kích hoạt (Trigger)**: Bộ lập lịch (Cron Scheduler) trong lõi Python kích hoạt `EmailSyncWorker` mỗi chu kỳ, hoặc kích hoạt thủ công khi UI bắn `SyncRequestedEvent`.
2. **Thực thi Độc Lập (Execution)**: Worker gọi API của Plugin cào mail. Hàm này chạy trên một `asyncio.Task` tách biệt khỏi Main Thread, hoàn toàn không Block luồng WebSocket đang stream text của Lõi AI.
3. **Phân tích Ngữ Nghĩa Bằng AI (Semantic Parsing)**: Gửi nội dung thô cho LLM (ưu tiên mô hình nhẹ/nhanh nhất cấu hình trong Settings) để nhận dạng và bóc tách thông tin tạo thành `EmailAnalysisDTO`.
4. **Lưu trữ & Đồng bộ Tự động (Autonomous Sync)**: Nếu LLM phát hiện sự kiện mới, lưu thẳng vào `CalendarEvent` với flag `source="auto_email"` thay vì bắt người dùng xác nhận thủ công.
5. **Phát Sự Kiện (Event Publishing)**: Đẩy gói `AutonomousSyncEvent` lên Event Bus để các component khác (như Alert Engine) cập nhật UI hoặc Notification.

### Luồng Nhắc Nhở Công Việc (TaskNotifierWorker)
1. **Quét định kỳ**: Cứ mỗi 60 giây, kiểm tra trong DB các công việc chưa hoàn thành có hạn chót trong 30 phút tới.
2. **Cảnh Báo (Alert)**: Phát `AlertTriggeredEvent(Urgency.HIGH/CRITICAL)` qua Event Bus.
3. **OS Notification**: Frontend Tauri bắt sự kiện Alert qua WebSocket và kích hoạt Native OS Notification trên máy người dùng.

---

## 3. Quy Tắc Xử Lý Lỗi & Thử Lại (Error Handling & Retry Rules)

Môi trường mạng của một Desktop App là không ổn định. Hệ thống phải được trang bị "Áo giáp" (Resiliency) để chịu đựng mọi loại lỗi.

### 3.1. Chiến Thuật Lùi Bước Cấp Số Nhân (Exponential Backoff)
Khi Worker gặp lỗi rớt mạng (Network Timeout) hoặc lỗi tạm thời (HTTP 500/502/503), cấm tuyệt đối việc quăng Exception làm sập luồng. Phải áp dụng Retry tự động:
- Thử lại lần 1: Đợi 1 giây.
- Thử lại lần 2: Đợi 2 giây.
- Thử lại lần 3: Đợi 4 giây.
- Thử lại lần 4: Đợi 8 giây.
- Tối đa thử 5 lần. Nếu vẫn tịt, ngắt kết nối để không làm nghẽn băng thông cục bộ.

### 3.2. Tôn Trọng Rate Limiting của Bên Thứ 3
Khi gọi API của OpenAI, Gmail hay Slack, nếu bị trả về lỗi **HTTP 429 (Too Many Requests)**:
- Ngay lập tức ngừng chọi Request. Đọc giá trị Header `Retry-After` từ Response (nếu có).
- Worker tự đình chỉ (Sleep) chính xác bằng số giây yêu cầu. Nếu API không trả về `Retry-After`, áp dụng cơ chế khóa cứng (Hard-sleep) 60 giây trước khi tiếp tục.

### 3.3. Hàng Đợi Lỗi Chết (Dead Letter Queue - DLQ)
Nếu sau mọi nỗ lực thử lại mà tác vụ vẫn thất bại (Ví dụ lỗi `HTTP 401 Unauthorized` do người dùng đổi mật khẩu Google làm Token hết hạn):
1. **Hủy Tác Vụ (Abort)**: Worker xóa task khỏi hàng đợi bộ nhớ.
2. **Ghi nhận (Audit)**: Lưu thông tin Task hỏng vào bảng `dead_letter_queue` trong SQLite để Developer có thể Debug sau.
3. **Báo cáo Lịch sự (Polite UI Notification)**: Publish một `SystemEvent(level="warning")`. Frontend sẽ nhận tín hiệu và hiện một chấm than màu vàng nhạt hoặc Toast cực nhỏ ở góc dưới màn hình ("Không thể đồng bộ Lịch do phiên đăng nhập hết hạn"). Tuyệt đối không ném hộp thoại báo Lỗi (Popup Dialog) ra giữa màn hình gây cản trở công việc của User.

---

## 4. Task Checklist Triển Khai Hệ Thống Worker

**Phía Backend Python:**
- [x] Cài đặt thư viện lập lịch `APScheduler` để quản lý luồng Cron Job cào dữ liệu định kỳ một cách chuyên nghiệp.
- [ ] Cài đặt thư viện `Tenacity` để thiết lập các Decorator Retry và Exponential Backoff một cách thanh lịch cho mọi hàm có nguy cơ dính Network Error.
- [x] Xây dựng module `WorkerManager` chịu trách nhiệm theo dõi, khởi chạy và quản lý các Job tập trung.
- [x] Khởi tạo bảng `dead_letter_events` (hoặc DLQ) trong CSDL SQLite.

**Phía Frontend Tauri:**
- [ ] Lắng nghe sự kiện Online/Offline từ API của hệ điều hành thông qua Tauri.
- [ ] Viết logic tự động gửi gói tin `NetworkRestoredEvent` lên Lõi Python khi người dùng có mạng trở lại, để các Worker bị đình chỉ lập tức Resume công việc.
