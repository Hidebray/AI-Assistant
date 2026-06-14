# Feature: Lịch nội bộ & Nhắc nhở (In-app Calendar & Notifications)

## Feature Overview

* **Mục đích**: Thay vì phụ thuộc hoàn toàn vào Google Calendar, hệ thống sử dụng một Lịch nội bộ lưu trong cơ sở dữ liệu SQLite để quản lý sự kiện. Một Worker (`CalendarNotifierWorker`) chạy ngầm mỗi phút để rà soát các sự kiện sắp diễn ra. Nếu sự kiện cách hiện tại $\le$ 5 phút, nó sẽ kích hoạt chuông cảnh báo.
* **Actor**: User (đặt lịch qua Chat), System (quét và nhắc nhở).
* **Business rules**: 
  - Chỉ cảnh báo các event có `is_deleted = False` và `is_notified = False`.
  - Khoảng thời gian để cảnh báo là: $0 < T_{start} - T_{now} \le 5\text{ phút}$.
  - Sau khi bắn thông báo, cập nhật ngay `is_notified = True` để chống trùng.
* **Dependencies**: Local SQLite (`CalendarEvent` table), `async_event_bus.py`, Alert Trigger System.

---

### Test Cases

#### Nhắc nhở sự kiện diễn ra trong 5 phút tới <TC-CAL-001>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-CAL-001                                             |
| Test Case       | Kiểm tra hệ thống tự động bắn cảnh báo (Toast) khi có sự kiện sẽ diễn ra trong vòng < 5 phút (Positive). |
| Related Feature | In-app Calendar                                        |
| Context         | Backend đang chạy, đồng hồ hệ thống chạy bình thường. |
| Input Data      | Một sự kiện được lưu trong DB với thời gian bắt đầu là (Hiện tại + 3 phút), `is_notified = False`. |
| Expected Output | Tại chu kỳ chạy tiếp theo của Worker (trong vòng 1 phút), màn hình hiển thị Toast Alert: "Sắp tới giờ sự kiện: [Tên sự kiện]". |
| Test Steps      | <ol><li>Vào Chat nhập: "Đặt lịch uống thuốc vào 3 phút nữa".</li><li>AI xác nhận đã tạo.</li><li>Ngồi chờ tối đa 1 phút.</li><li>Quan sát Toast Alert nhảy lên UI.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |

#### Bỏ qua sự kiện đã thông báo (Chống Spam) <TC-CAL-002>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-CAL-002                                             |
| Test Case       | Kiểm tra Worker cập nhật state `is_notified` và không báo lại lần 2 (Negative). |
| Related Feature | In-app Calendar                                        |
| Context         | TC-CAL-001 vừa pass, event "uống thuốc" vẫn đang nằm trong khoảng < 5 phút. |
| Input Data      | Sự kiện có `is_notified = True`. |
| Expected Output | Ở chu kỳ 60s tiếp theo, không có thông báo nào bị lặp lại. |
| Test Steps      | <ol><li>Ngay sau khi nhận được Toast từ bước tạo lịch ở TC-CAL-001.</li><li>Tiếp tục đợi thêm 1 chu kỳ phút nữa.</li><li>Quan sát xem có bị nhảy Toast lần 2 không.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |

#### Ranh giới thời gian đúng 5 phút <TC-CAL-003>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-CAL-003                                             |
| Test Case       | Kiểm thử vùng cận ranh giới của điều kiện cảnh báo thời gian (Boundary). |
| Related Feature | In-app Calendar                                        |
| Context         | Backend đang chạy. |
| Input Data      | Tạo 2 sự kiện: Event A (Hiện tại + 5 phút 05 giây), Event B (Hiện tại + 4 phút 55 giây). |
| Expected Output | Event B được cảnh báo ngay chu kỳ quét đầu tiên. Event A bị bỏ qua, và phải đợi đến chu kỳ quét tiếp theo (khi thời gian rớt xuống < 5 phút) mới báo. |
| Test Steps      | <ol><li>Sử dụng tool trực tiếp hoặc script để chèn 2 record có time chính xác như mô tả vào DB.</li><li>Quan sát terminal log.</li><li>Worker sẽ in log "Found upcoming event" cho Event B.</li><li>Đợi 1 phút sau, Worker in log cho Event A.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |

#### Bỏ qua sự kiện đã quá hạn <TC-CAL-004>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-CAL-004                                             |
| Test Case       | Worker không quét các sự kiện mà `start_time` đã nhỏ hơn giờ hiện tại (Negative). |
| Related Feature | In-app Calendar                                        |
| Context         | Cố ý quên tick `is_notified` cho một sự kiện trong quá khứ. |
| Input Data      | Sự kiện C (Hiện tại - 10 phút), `is_notified = False`. |
| Expected Output | Không có sự kiện nào được nhắc nhở. |
| Test Steps      | <ol><li>Chèn data giả vào SQLite cho Event C.</li><li>Đợi worker quét.</li><li>Đảm bảo UI không bị hiện Toast rác của quá khứ.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |
