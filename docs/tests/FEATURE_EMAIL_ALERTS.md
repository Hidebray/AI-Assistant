# Feature: Quét Email Ngầm & Cảnh báo (Background Email Ingestion & Alerts)

## Feature Overview

* **Mục đích**: Hệ thống sử dụng một Worker (`EmailScannerWorker`) chạy ngầm định kỳ mỗi 60 giây để quét API Gmail và lấy về các email chưa đọc. Sau đó, nó sử dụng **LLM (Mô hình Ngôn ngữ Lớn)** để phân tích ngữ nghĩa của email. Nếu nhận diện được nội dung chứa sự kiện Lịch (họp, cuộc hẹn) hoặc Task, hệ thống tự động bóc tách (extract) và tạo dữ liệu trực tiếp vào database (`CalendarEvent`/`Task`), đồng thời gửi một OS Notification (Cảnh báo Native) lên màn hình người dùng.
* **Actor**: System (Background Worker), LLMFactory, AlertEngine.
* **Business rules**: 
  - Chỉ quét những email mang cờ `unread`.
  - Giới hạn quét tối đa 5 email mới nhất mỗi lần để tiết kiệm API Quota.
  - Phân tích bằng Prompt thiết kế sẵn để trích xuất `EmailAnalysisDTO`.
  - Tự động gán nguồn `source_origin="auto_email"`.
* **Dependencies**: `EmailPlugin` (Cung cấp OAuth Token), EventBus, `LLMFactory`.

---

### Test Cases

#### Cảnh báo Email VIP <TC-EML-001>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-EML-001                                             |
| Test Case       | Kiểm thử cảnh báo khi có email gửi từ một địa chỉ trong VIP list (Positive). |
| Related Feature | Email Alerts                                           |
| Context         | User đã kết nối Google Account và Backend đang chạy. App Frontend đang mở. |
| Input Data      | Gửi 1 email đến hộp thư được theo dõi với người gửi là `ceo@company.com` (theo mock data). |
| Expected Output | Trong tối đa 60 giây, ứng dụng hiển thị Toast Notification: "Email khẩn từ ceo@company.com: [Tiêu đề]". |
| Test Steps      | <ol><li>Bật Backend để worker bắt đầu chạy ngầm.</li><li>Gửi một email test từ địa chỉ ceo@company.com tới tài khoản đang login.</li><li>Đảm bảo email ở trạng thái Unread.</li><li>Ngồi chờ không tương tác gì ở giao diện AAA.</li><li>Quan sát xem thông báo AlertTriggeredEvent có bắn lên không.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |

#### Phân Tích Sự Kiện và Báo Cáo Native <TC-EML-002>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-EML-002                                             |
| Test Case       | Kiểm thử tự động đồng bộ Lịch từ LLM Analysis (Autonomous Sync). |
| Related Feature | Email Alerts & OS Notifications                        |
| Context         | User đã kết nối Google Account và cấu hình LLM hợp lệ. |
| Input Data      | Gửi 1 email với nội dung mời họp cụ thể (Ví dụ: "Hẹn anh 3h chiều nay họp về tiến độ dự án"). |
| Expected Output | LLM nhận diện được giờ họp và tự động lưu vào bảng `calendar_events`. Đồng thời bắn Native OS Notification: "Đã tự động lên lịch: [Tiêu đề] lúc [Giờ]". |
| Test Steps      | <ol><li>Gửi email mời họp.</li><li>Không tương tác gì với UI AAA.</li><li>Đợi tối đa 60s cho cronjob chạy.</li><li>Kiểm tra xem hệ điều hành Windows/macOS có bắn thông báo Native Notification không.</li><li>Mở UI, gõ `/calendar` để xem sự kiện đã được lưu chưa.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |

#### Lọc trùng lặp cảnh báo (Deduplication) <TC-EML-003>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-EML-003                                             |
| Test Case       | Kiểm thử cơ chế Deduplication của AlertEngine (Boundary/Negative). |
| Related Feature | Email Alerts                                           |
| Context         | Backend đang chạy, có 1 email khẩn cấp đang ở trạng thái Unread. |
| Input Data      | Email khẩn cấp (có từ URGENT) không bị thay đổi trạng thái sang Read sau khi hệ thống quét lần 1. |
| Expected Output | Hệ thống chỉ thông báo 1 lần duy nhất cho email đó trong khoảng thời gian TTL (5 phút). Ở các chu kỳ 60s tiếp theo, AlertEngine sẽ báo log "Duplicate alert suppressed" và không bắn lên UI nữa. |
| Test Steps      | <ol><li>Giữ nguyên một email khẩn cấp chưa đọc trong inbox.</li><li>Theo dõi Backend log trong 3 chu kỳ liên tiếp (khoảng 3 phút).</li><li>Chu kỳ 1: Thấy thông báo bắn lên UI.</li><li>Chu kỳ 2 & 3: Thấy log ghi nhận "Duplicate alert suppressed", UI không hiện thông báo trùng.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |

#### Bỏ qua email bình thường <TC-EML-004>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-EML-004                                             |
| Test Case       | Kiểm thử hệ thống bỏ qua email không thuộc VIP và không có keyword khẩn cấp. |
| Related Feature | Email Alerts                                           |
| Context         | Backend đang chạy. |
| Input Data      | Gửi một email "Chúc mừng năm mới" từ `someone@example.com`. |
| Expected Output | Worker vẫn lấy email về nhưng AlertEngine đánh giá là is_matched=False. Không có Alert nào được gửi lên UI. |
| Test Steps      | <ol><li>Gửi email bình thường.</li><li>Đợi 60s.</li><li>Quan sát log và UI (Không có gì thay đổi).</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |

#### Chưa cấp quyền OAuth (Negative) <TC-EML-005>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-EML-005                                             |
| Test Case       | Worker xử lý ra sao khi file `token.json` (OAuth) không tồn tại. |
| Related Feature | Email Alerts                                           |
| Context         | Xóa file `token.json` trong thư mục gốc. |
| Input Data      | N/A |
| Expected Output | Worker log ra debug message "No valid credentials. Skipping." Hệ thống không crash. |
| Test Steps      | <ol><li>Tắt backend.</li><li>Xóa file token.json.</li><li>Bật backend lên lại.</li><li>Kiểm tra log của EmailScannerWorker.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |
