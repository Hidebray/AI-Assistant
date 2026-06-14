# Đặc tả Nghiệp vụ Chế độ Ngoại tuyến & Lệnh Tĩnh (Offline Fallback & Static Commands)

Tài liệu này đặc tả quy tắc nghiệp vụ cho **Chế độ Giảm thiểu Có kiểm soát (Graceful Degradation)** của hệ thống. Khi mất kết nối Internet hoặc Cloud LLM bị sập, AAA không được phép ngừng hoạt động. Thay vào đó, hệ thống tự động chuyển sang chế độ `Rule-Based Fallback`, cho phép người dùng điều khiển trợ lý bằng các cú pháp tĩnh (Regex Commands) để thao tác trực tiếp với cơ sở dữ liệu SQLite cục bộ.

---

## 1. User Stories (Câu Chuyện Người Dùng)

- **US01 (Tra cứu không cần mạng)**: *Là một người hay đi công tác*, tôi muốn vẫn có thể xem được lịch trình ngày mai hoặc đọc lại các ghi chú cũ kể cả khi đang ngồi trên máy bay không có Wifi, *để* công việc không bị gián đoạn.
- **US02 (Ghi chú nhanh ngoại tuyến)**: *Là một nhà nghiên cứu*, tôi muốn có thể tạo ra các ghi chú (nhớ tạm) vào hệ thống ngay lập tức bằng các cú pháp ngắn gọn, *để* khi có mạng, AI tự động nạp các ghi chú này vào Long-term Memory.
- **US03 (Nhận diện trạng thái mạng)**: *Là một người dùng thông thường*, tôi muốn UI hiển thị rõ ràng khi nào AI đang ở chế độ Offline và hướng dẫn tôi các câu lệnh tĩnh có thể dùng, *để* tôi không bị bối rối vì sao AI không phản hồi như người bình thường.

---

## 2. Luồng Xử Lý Mất Mạng (Graceful Degradation Flow)

Khác với chế độ Online nơi tin nhắn chạy qua Lõi AI (AgentCore) để phân tích ngữ nghĩa tự nhiên, ở chế độ Offline, đường ống dữ liệu được định tuyến lại.

1. **Phát hiện Ngoại tuyến (Offline Detection & Graceful Degradation)**: 
   - Thay vì dùng Python ping mạng liên tục gây hao pin, Frontend (Tauri) sẽ trực tiếp sử dụng OS Network API (qua plugin `tauri-plugin-network` hoặc sự kiện DOM `navigator.onLine`) để phát hiện rớt mạng ngay lập tức.
   - Khi mất mạng, Frontend gửi một gói tin `{"type": "NETWORK_UPDATE", "is_online": false}` qua WebSocket cho Backend, đồng thời chuyển Header sang màu xám/vàng kèm thông báo.
   - **Đặc biệt**: Hệ thống áp dụng mẫu thiết kế *Chain of Responsibility* (Cloud LLM -> Local Ollama -> Fallback Engine). Ngay cả khi Frontend báo đang Online nhưng CẢ Cloud lẫn Local LLM đều từ chối kết nối (chết hoàn toàn), `ChatWorker` sẽ bắt ngoại lệ và tự động chuyển hướng luồng dữ liệu sang chế độ Fallback mượt mà.
2. **Định tuyến (Routing)**:
   - Khi nhận tin nhắn mới từ UI, thay vì ném vào LLM, `ChatWorker` kiểm tra cờ `is_online` hoặc bắt ngoại lệ từ quá trình gọi LLM.
   - Nếu sập mạng hoặc sập AI, tin nhắn được chuyển thẳng cho module `FallbackEngine`.
3. **Phân tích Cú pháp (Regex Parsing)**:
   - `FallbackEngine` kiểm tra ký tự đầu tiên. Nếu không phải là dấu `/`, nó trả về một tin nhắn hệ thống (System Message): *"Trợ lý đang mất kết nối mạng. Vui lòng nhập dấu '/' để sử dụng các lệnh cục bộ (VD: /calendar, /note, /task)."*
   - Nếu bắt đầu bằng `/`, nó dùng Biểu thức chính quy (Regex) để trích xuất Lệnh (Command) và Tham số (Arguments).

---

## 3. Danh Mục Lệnh Tĩnh (Static Commands Registry)

Tương tự như Plugin, các Lệnh (Commands) cũng phải tuân thủ nguyên tắc mở rộng OCP. Mỗi lệnh là một class định nghĩa sẵn Regex Pattern và hàm Execute tác động trực tiếp lên DB.

### 3.1. Nhóm Lệnh Tra Cứu (Read-Only)
Thao tác với dữ liệu đã lưu trong SQLite.
- `/calendar [ngày]`: Truy vấn bảng `calendar_events`.
  - Tham số: `hom_nay`, `ngay_mai`, hoặc định dạng `dd/mm`. Mặc định là hôm nay.
  - Output: Text dạng Markdown liệt kê lịch họp.
- `/task`: Truy vấn bảng `tasks` để xem danh sách công việc.
  - Tham số bổ sung: `--all` (xem tất cả).
  - Output: Danh sách công việc đang chờ xử lý.

### 3.2. Nhóm Lệnh Nhập Liệu (Write)
Lưu trữ tạm thời hoặc tạo mới dữ liệu.
- `/note [nội_dung]`: Lưu nội dung vào bảng `memory_nodes` với tag `offline_note`.
  - Ví dụ: `/note Nhớ mua sữa lúc đi làm về`.
- `/task --add [nội_dung]`: Thêm nhanh một công việc vào danh sách.
- `/task --done [từ khóa]`: Đánh dấu một công việc là hoàn thành.

---

## 4. Đặc Tả Class `FallbackEngine`

### Kiến trúc Hoạt Động
- `FallbackEngine` duy trì một danh sách (Registry) các đối tượng `ICommand`.
- Mỗi `ICommand` phải định nghĩa:
  - `pattern`: Regex String (VD: `^/calendar\s*(?P<date>.*)?$`)
  - `help_text`: Đoạn văn bản hướng dẫn sử dụng (song ngữ tùy theo language).
  - `execute(args, user_id, language)`: Hàm thực thi gọi thẳng vào Database thông qua Interface (không qua LLM). Hỗ trợ i18n để trả lời tiếng Anh/Việt.

### Mã Mẫu (Pseudo-code)
```python
class CalendarCommand(ICommand):
    pattern = r"^/calendar\s*(?P<date>.*)?$"
    help_text = "/calendar [ngay_mai] - Tra cứu lịch trình cục bộ."

    def execute(self, match_dict, user_id: str, language: str = "vi") -> str:
        date_str = match_dict.get('date', '').strip().lower()
        # Logic tính toán target_date (hôm nay, ngày mai...)
        
        # Gọi trực tiếp DAO để Query SQLite
        events = repo.get_events_by_date(target_date)
        
        if not events:
            return f"Không có lịch trình nào cho {target_date}."
            
        # Format kết quả thủ công (Vì không có LLM để sinh văn bản mượt mà)
        response = f"**Lịch trình {target_date}:**\n"
        for e in events:
            response += f"- {e.start_time}: {e.title}\n"
        return response
```

---

## 5. Tích Hợp Lại Khi Có Mạng (Online Restoration)

Ngay khi `NetworkMonitor` báo cáo có mạng trở lại (`is_online = True`):
1. **Khôi phục UI**: Xóa banner cảnh báo Ngoại tuyến.
2. **Phân loại Ghi chú**: Lõi AI quét các record `/note` vừa được tạo lúc Offline, đẩy chúng qua LLM để trích xuất (Consolidate) thành các Facts/Preferences chuẩn mực và cập nhật lại bảng `memory_nodes`.

---

## 6. Task Checklist Triển Khai Chế Độ Ngoại Tuyến

- [x] Lập trình Background Task `NetworkMonitor` bên trong Tauri (DOM navigator hoặc plugin mạng của OS), bắn tín hiệu Websocket lên Backend.
- [x] Thiết kế Component React `OfflineBanner` trên đỉnh của giao diện Main Chat để thông báo trạng thái.
- [x] Viết module `FallbackEngine` với kiến trúc OCP, cho phép nạp mảng các đối tượng `ICommand` hỗ trợ i18n (`language` parameter).
- [x] Lập trình các Command thiết yếu ban đầu: `CalendarCommand` (/calendar), `NoteCommand` (/note), `TaskCommand` (/task) sử dụng Regex thuần túy (`re.match`).
- [x] Tích hợp `FallbackEngine` vào `ChatWorker`: Bắt ngoại lệ từ LLM Adapter khi mất mạng và tự động định tuyến văn bản xuống Regex Parser.
