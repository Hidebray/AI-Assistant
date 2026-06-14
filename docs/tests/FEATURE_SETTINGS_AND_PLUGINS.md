# Feature: Cài đặt Hệ thống & Quản lý Plugin (Settings & Plugins)

## Feature Overview

* **Mục đích**: Cung cấp giao diện và API để quản lý trạng thái của các Plugin (Bật/Tắt), cập nhật API Keys cho LLM (OpenAI, Gemini), và cấp phép (Permissions) cho các công cụ (như quyền truy cập mạng, quyền đọc ghi file).
* **Actor**: End User.
* **Business rules**: 
  - API Keys được mã hóa trước khi lưu vào SQLite.
  - Khi một Plugin bị tắt, ToolExecutor sẽ không load công cụ của Plugin đó vào danh sách Tool cung cấp cho LLM.
  - Khi quyền của Plugin bị giới hạn (ví dụ: cấm `network`), mọi thao tác gọi mạng từ plugin đó sẽ bị chặn và quăng Exception.
* **Dependencies**: `SettingsManager`, Local SQLite, `ToolExecutor`.

---

### Test Cases

#### Tắt quyền truy cập Mạng của Plugin <TC-SET-001>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-SET-001                                             |
| Test Case       | Vô hiệu hóa permission `network` của EmailPlugin và gọi tool, kỳ vọng báo lỗi (Security). |
| Related Feature | Settings                                               |
| Context         | Giao diện Settings đang mở, tab Plugins.               |
| Input Data      | Gạt tắt quyền "Network Access" của `Email Plugin`. Chat: "Quét email cho tôi." |
| Expected Output | LLM cố gắng gọi tool quét email nhưng ToolExecutor chặn lại vì thiếu quyền, trả về lỗi "Permission Denied: Network access is disabled cho plugin này". |
| Test Steps      | <ol><li>Vào Settings -> Plugins -> Email Plugin.</li><li>Tắt quyền Network.</li><li>Quay lại màn hình Chat.</li><li>Yêu cầu AI quét email mới.</li><li>Kiểm tra phản hồi của AI.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |

#### Cập nhật API Key mới cho OpenAI <TC-SET-002>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-SET-002                                             |
| Test Case       | Lưu API key bị sai và kiểm tra kết nối có bị từ chối không, sau đó sửa lại key đúng (Negative/Positive). |
| Related Feature | Settings                                               |
| Context         | Mạng internet ổn định.                                 |
| Input Data      | Lần 1: Key rác `sk-fake-key-123`. Lần 2: Key thật.    |
| Expected Output | Lần 1: AI báo lỗi Authentication Error (401) hoặc tự động fallback qua Ollama. Lần 2: Chat mượt mà, phản hồi siêu tốc từ Cloud. |
| Test Steps      | <ol><li>Vào Settings -> LLM Config.</li><li>Nhập key rác, lưu lại.</li><li>Chat thử và kiểm tra log/UI xem lỗi 401.</li><li>Nhập key chuẩn, lưu lại.</li><li>Chat lại câu đó và nhận phản hồi bình thường.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |

#### Bật/Tắt hoàn toàn một Plugin <TC-SET-003>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-SET-003                                             |
| Test Case       | Khi tắt một Plugin, Agent không còn nhận diện được Tool của Plugin đó (Functional). |
| Related Feature | Settings                                               |
| Context         | WebSearch Plugin đang bật.                             |
| Input Data      | Nút toggle "Enable" của WebSearch Plugin -> OFF. Chat: "Tìm kiếm thời tiết hôm nay". |
| Expected Output | Agent báo: "Tôi không có công cụ tìm kiếm trên mạng để trả lời câu hỏi này." do WebSearch Plugin đã bị gỡ khỏi ToolList. |
| Test Steps      | <ol><li>Vào Settings, tắt Plugin WebSearch.</li><li>Yêu cầu Agent tìm kiếm thông tin mới nhất.</li><li>Kiểm tra phản hồi của Agent (từ chối do thiếu tool).</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |

#### Xóa toàn bộ dữ liệu (Factory Reset) <TC-SET-004>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-SET-004                                             |
| Test Case       | Xác nhận chức năng Xóa toàn bộ dữ liệu hoạt động chính xác và an toàn. |
| Related Feature | Settings                                               |
| Context         | Giao diện Settings đang mở, phần Cài đặt Chung.        |
| Input Data      | Gõ sai chữ "DELETE" và gõ đúng chữ "DELETE".          |
| Expected Output | Gõ sai: Nút xác nhận bị khóa. Gõ đúng: Nhấn xác nhận, hệ thống gọi API xóa dữ liệu, đăng xuất và đẩy về trang đăng nhập. |
| Test Steps      | <ol><li>Cuộn xuống Khu vực Nguy hiểm.</li><li>Nhấn Khôi phục cài đặt gốc.</li><li>Gõ "RESET" (nút vẫn khóa).</li><li>Gõ "DELETE" (nút mở khóa) và xác nhận.</li><li>Kiểm tra trạng thái đăng xuất và DB trống.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |

#### Thay đổi Mật khẩu (Change Password) <TC-SET-005>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-SET-005                                             |
| Test Case       | Xác thực quy trình thay đổi mật khẩu tài khoản quản trị. |
| Related Feature | Settings                                               |
| Context         | Giao diện Settings đang mở, phần Cài đặt Chung.        |
| Input Data      | Lần 1: Sai mật khẩu cũ. Lần 2: Mật khẩu mới quá ngắn (<6 ký tự). Lần 3: Pass mới và Pass xác nhận không khớp. Lần 4: Đúng tất cả. |
| Expected Output | Lỗi Validation xuất hiện ở Lần 1, 2, 3. Lần 4 thành công, hiển thị Toast xanh và cho phép đăng nhập lại bằng mật khẩu mới. |
| Test Steps      | <ol><li>Nhấn "Cập nhật mật khẩu" trong phần Tài khoản.</li><li>Nhập sai pass cũ -> Toast đỏ.</li><li>Nhập pass mới 3 ký tự -> Chữ đỏ cảnh báo độ dài.</li><li>Nhập pass xác nhận sai -> Chữ đỏ cảnh báo không khớp.</li><li>Nhập đúng chuẩn và xác nhận.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |
