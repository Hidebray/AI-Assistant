# Đặc tả Phân loại Cảnh báo & Thông báo đẩy (Alert Engine Specs)

Tài liệu này đặc tả quy tắc nghiệp vụ của Hệ thống Cảnh báo (Alert Engine). Nằm ở Lõi AI, hệ thống này đóng vai trò như một "Người gác cổng" (Gatekeeper) thông minh, chịu trách nhiệm lọc hàng ngàn sự kiện (dữ liệu ngầm) mỗi ngày để quyết định chính xác xem thông tin nào xứng đáng làm gián đoạn sự tập trung của người dùng.

---

## 1. User Stories (Câu Chuyện Người Dùng)

- **US01 (Bảo vệ sự tập trung tối đa)**: *Là một lập trình viên đang code*, tôi muốn AI không bao giờ được phép làm phiền tôi bằng các thông báo nổi (Pop-ups) về email quảng cáo hay tin tức lặt vặt, *để* tôi có thể duy trì luồng công việc (flow state) một cách trọn vẹn mà không bị bực mình.
- **US02 (Không bỏ lỡ việc sinh tử)**: *Là một quản lý dự án*, tôi muốn AI lập tức hất một thông báo nổi kèm âm thanh (Ping alert) khi có email từ Giám đốc (VIP) gửi đến, *để* tôi có thể phản hồi ngay lập tức dù đang ẩn toàn bộ các cửa sổ làm việc.
- **US03 (Nhắc nhở chủ động đúng lúc)**: *Là một người dùng hay quên*, tôi muốn hệ thống tự động bật một thông báo nhỏ gọn kèm nút thao tác nhanh "Mở Zoom" đúng 15 phút trước khi một cuộc họp diễn ra, *để* tôi kịp thời khởi động camera và chuẩn bị tài liệu.

---

## 2. Phân Loại Mức Độ Khẩn Cấp (Urgency Levels)

Hệ thống phân chia mọi luồng dữ liệu thu thập được thành 4 cấp độ (Urgency Levels) cứng. Mỗi cấp độ sẽ ra lệnh cho Giao diện React/Tauri kích hoạt một hành vi (Behavior) khác biệt hoàn toàn.

| Cấp Độ | Mức độ gián đoạn | Phản ứng của Hệ thống & Giao diện (Tauri) |
| :--- | :--- | :--- |
| **Critical** (Khẩn cấp) | Tối đa (Bắt buộc nhìn) | Trượt Toast Notification ra góc màn hình kèm rung nhẹ (Shake Animation). Kích hoạt âm thanh hệ thống (Ping). Chèn một dòng thông báo màu đỏ đập vào mắt người dùng ngay giữa khung Main Chat. |
| **High** (Cao) | Trung bình | Trượt Toast Notification vào màn hình một cách êm ái (Không kèm âm thanh). Tồn tại trong 10-15 giây rồi tự động biến mất. Không làm phiền trải nghiệm đọc chữ. |
| **Normal** (Bình thường) | Rất thấp (Không cắt ngang) | **Tuyệt đối không bật cửa sổ Toast**. Thay vào đó, tăng biến đếm số lượng thông báo chưa đọc (Badge counter màu đỏ) đính lên Icon AAA ở dưới Khay Hệ Thống (Taskbar) hoặc trên thanh Menu Sidebar. |
| **Low / Silent** (Tàng hình) | Mức Không (Zero) | Không kích hoạt bất cứ tín hiệu UI nào. Thông tin chỉ được lưu âm thầm vào kho dữ liệu SQLite để Lõi AI có tài nguyên tham khảo sau này. Áp dụng cho: Email spam, Newsletter, Sự kiện lịch của đồng nghiệp. |

---

## 3. Đặc Tả Tập Quy Tắc Đánh Giá (Rule Sets)

### 3.1. Tuân Thủ Nghiêm Ngặt Nguyên Tắc OCP (Open/Closed Principle)
Alert Engine không được phép code cứng (hard-code) một mớ lệnh if-else rối rắm.
- Cấu trúc hệ thống tuân theo Design Pattern **Chain of Responsibility** (Hoặc Rule Engine).
- Mọi Quy tắc (Rule) là một class bằng Python hoàn toàn độc lập, kế thừa từ Interface chuẩn `IAlertRule`. Interface này chỉ ép buộc triển khai 1 hàm duy nhất: `evaluate(event_data) -> RuleResult`.
- Nhờ OCP, đội ngũ kỹ sư sau này có thể dễ dàng thiết lập hàng chục Rule mới (như `StockPriceCrashRule`, `WeatherStormRule`) bằng cách vứt file `.py` mới vào thư mục quy tắc mà không phải sửa một dòng code nào trong lõi vận hành của Engine.

### 3.2. Cấu Trúc Trả Về (RuleResult)
Khi một sự kiện chạy ngang qua một Rule, nó bị đánh giá và trả ra một `RuleResult` chứa:
- `is_matched`: boolean (Sự kiện này có khớp với quy tắc này không?)
- `urgency`: Enum (Critical, High, Normal, Low)
- `weight`: integer (Trọng số độ tin cậy. Nếu một sự kiện bị 2 Rules đánh giá ra 2 mức Urgency khác nhau, Engine sẽ lấy mức Urgency của Rule có `weight` cao hơn để quyết định).

### 3.3. Các Ví Dụ Quy Tắc Nghiệp Vụ Lõi (Core Business Rules)

#### Rule 1: Nhắc nhở Sự kiện Lịch (Time-based Rule)
- **Tên class**: `UpcomingMeetingRule` (Weight: 80)
- **Mục tiêu**: Nhắc nhở trước giờ họp.
- **Điều kiện kích hoạt**: Rule này lắng nghe nhịp gõ của đồng hồ hệ thống, liên tục lôi `start_time` trong bảng `calendar_events` ra trừ cho giờ hiện tại (UTC).
- **Logic đánh giá**: 
  ```python
  time_diff = event.start_time - current_utc_time
  if 0 < time_diff <= 15 minutes:
      return RuleResult(is_matched=True, urgency=Urgency.HIGH, message="Sắp tới giờ họp: [Title]", action="OPEN_URL")
  return RuleResult(is_matched=False)
  ```

#### Rule 2: Phễu Lọc Email Quan Trọng (Keyword/Sender-based Rule)
- **Tên class**: `VIPEmailRule` (Weight: 95 - Quyền sinh sát tối cao)
- **Mục tiêu**: Bắt chết các email từ sếp hoặc mang tính chất hỏa tốc.
- **Điều kiện kích hoạt**: Lắng nghe luồng dữ liệu đổ về từ `NewEmailArrivedEvent` do Background Worker gửi lên.
- **Logic đánh giá**: 
  ```python
  is_vip = email.sender_address in UserSettings.get("vip_emails_list")
  is_urgent = "URGENT" in email.subject.upper() or "ASAP" in email.subject.upper()
  
  if is_vip or is_urgent:
      return RuleResult(is_matched=True, urgency=Urgency.CRITICAL, message="Email khẩn từ [Sender]")
  elif "UNSUBSCRIBE" in email.body.upper(): # Phát hiện Email Marketing
      return RuleResult(is_matched=True, urgency=Urgency.LOW)
  ```

---

## 4. Cơ Chế Tích Hợp Event Bus Bất Đồng Bộ

Làm thế nào để hệ thống Backend Python kích hoạt được giao diện React hiển thị thông báo?

1. Worker cào dữ liệu thành công -> Nó mù quáng đẩy `RawEvent` lên IEventBus nội bộ.
2. `AlertEngine` (Vốn dĩ đang subscribe lắng nghe IEventBus) chộp lấy sự kiện thô này.
3. Engine ném sự kiện lướt qua toàn bộ mảng `rules_list` đang nạp trong RAM.
4. Nếu có ít nhất 1 Rule trả về `Matched` với cấp độ từ `High` trở lên, Engine sẽ lập tức đúc một sự kiện mệnh lệnh mới tên là `AlertTriggeredEvent(urgency, message, action_payload)`. Sau đó phát (publish) ngược lại sự kiện này lên Event Bus.
5. Tauri WebSocket Proxy nhận diện được `AlertTriggeredEvent`, nó đẩy gói tin JSON qua cho tầng Frontend React.
6. React nhận Packet, kích hoạt Component Timeline GSAP để render Toast Notification ra góc phải màn hình Desktop.

---

## 5. Task Checklist Triển Khai Alert Engine

- [ ] Định nghĩa Interface trừu tượng `IAlertRule` và cấu trúc DTO `RuleResult` tại module Domain.
- [ ] Lập trình class lõi `AlertEngine` đóng vai trò là "Container" thu thập danh sách các Rules và quản lý vòng lặp `Evaluate()` với logic so sánh Trọng số (Weight).
- [ ] Cài đặt class `UpcomingMeetingRule` đảm trách tính toán toán học về mốc thời gian (`datetime`).
- [ ] Cài đặt class `VIPEmailRule` bóc tách String / Regex tốc độ cao.
- [ ] Lập trình cơ chế Chống Spam Trùng Lặp (Deduplication / Debounce Cache) ngay trong Engine để phòng ngừa việc Engine bắn liên thanh 10 thông báo giống hệt nhau ra UI chỉ vì 1 email.
- [ ] Liên kết `AlertEngine` vào khối khởi tạo Dependency Injection (DI) lúc App khởi động để đảm bảo nó luôn sống và gắn chặt vào Event Bus.
