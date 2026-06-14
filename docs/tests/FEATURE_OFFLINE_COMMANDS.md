# Feature: Fallback Lệnh Ngoại Tuyến (Offline Commands)

## Feature Overview

* **Mục đích**: Cung cấp giải pháp dự phòng cuối cùng (Graceful Degradation). Khi cả kết nối Cloud LLM lẫn Local LLM đều thất bại (System down), người dùng vẫn có thể thao tác với cơ sở dữ liệu và hệ thống thông qua các câu lệnh tĩnh (Prefix `/`).
* **Actor**: FallbackEngine.
* **Business rules**: 
  - Lệnh được kích hoạt khi chuỗi chat bắt đầu bằng dấu `/`.
  - Hỗ trợ các lệnh: `/calendar` (xem lịch), `/note` (tạo ghi chú).
  - Parser dựa trên Regex, trích xuất dữ liệu và tương tác thẳng với DB mà không qua LLM.
* **Dependencies**: `FallbackEngine`, Local SQLite.

---

### Test Cases

#### Gõ lệnh tĩnh `/calendar` khi ngoại tuyến <TC-OFF-001>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-OFF-001                                             |
| Test Case       | Kiểm tra FallbackEngine bắt đúng Regex và trả về danh sách lịch trình khi LLM chết (Positive). |
| Related Feature | Offline Commands                                       |
| Context         | AgentCore gặp lỗi toàn tập (Tắt cả mạng lẫn Ollama). |
| Input Data      | Gõ: `/calendar` |
| Expected Output | Giao diện Chat hiển thị danh sách các sự kiện sắp tới được query trực tiếp từ SQLite (dưới dạng text markdown đơn giản). |
| Test Steps      | <ol><li>Ép lỗi LLM.</li><li>Gõ `/calendar` vào thanh chat.</li><li>Nhấn Enter.</li><li>Quan sát kết quả trả về.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |

#### Tạo ghi chú bằng lệnh tĩnh `/note` <TC-OFF-002>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-OFF-002                                             |
| Test Case       | Kiểm tra tính năng thêm ghi chú mới bằng Regex (Positive). |
| Related Feature | Offline Commands                                       |
| Context         | Hệ thống ngoại tuyến. |
| Input Data      | Gõ: `/note Mua sữa và trứng vào buổi chiều`           |
| Expected Output | Hệ thống trích xuất nội dung sau từ khóa `/note`, lưu vào DB và trả về: "Đã lưu ghi chú thành công." |
| Test Steps      | <ol><li>Nhập lệnh `/note Mua sữa...`</li><li>Gửi tin nhắn.</li><li>Kiểm tra thông báo xác nhận.</li><li>Dùng DB Browser xem bảng Notes xem đã có dòng dữ liệu mới chưa.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |

#### Lệnh tĩnh không tồn tại hoặc sai cú pháp <TC-OFF-003>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-OFF-003                                             |
| Test Case       | Kiểm tra độ robust của Regex Parser khi gõ chuỗi linh tinh (Boundary/Negative). |
| Related Feature | Offline Commands                                       |
| Context         | Đang ở trạng thái ngoại tuyến. |
| Input Data      | Gõ: `/not_exist something` hoặc `/calendar ???`           |
| Expected Output | Hệ thống trả về lỗi (tùy thuộc vào system_language): "Không nhận diện được lệnh. Các lệnh hỗ trợ: /calendar, /note." (Tiếng Việt) hoặc "Command not recognized. Available commands: /calendar, /note." (Tiếng Anh). Không bị crash. |
| Test Steps      | <ol><li>Gõ các lệnh sai cú pháp.</li><li>Nhấn gửi.</li><li>Kiểm tra thông báo lỗi có mang tính hướng dẫn không.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |
