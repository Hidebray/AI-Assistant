# TỔNG QUAN DỰ ÁN: AUTONOMOUS AI ASSISTANT (AAA)

---

# 1. BỐI CẢNH VÀ MỤC TIÊU DỰ ÁN

Dự án **Autonomous AI Assistant (AAA)** được hình thành nhằm giải quyết tình trạng **“quá tải nhận thức” (Cognitive Overload)** của người dùng máy tính cá nhân trong kỷ nguyên số.

Hiện nay, các đối tượng như sinh viên, nhân viên văn phòng và lập trình viên phải liên tục thực hiện thao tác **chuyển đổi ngữ cảnh (Context Switching)** giữa hàng loạt ứng dụng phân mảnh như:

- Email
- Lịch cá nhân
- Phần mềm quản lý công việc
- Công cụ nhắn tin
- Trình duyệt

Sự phân mảnh này không chỉ làm giảm hiệu suất làm việc mà còn:

- Gia tăng áp lực nhận thức
- Tăng nguy cơ bỏ sót thông tin
- Gây lỗi thao tác
- Dẫn đến trễ hạn công việc

## Mục tiêu của dự án

AAA được xây dựng như một **Tác tử Trí tuệ Nhân tạo Tự trị (Autonomous AI Agent)** hoạt động ngầm trên môi trường Desktop.

Khác với các chatbot truyền thống chỉ phản hồi thụ động khi được yêu cầu, AAA đóng vai trò là:

- Trợ lý trung gian thông minh
- Bộ điều phối thông tin tự động
- Hệ thống hỗ trợ quyết định cá nhân

Hệ thống có khả năng:

- Tự động thu thập dữ liệu
- Phân tích ngữ cảnh
- Đồng bộ thông tin
- Chủ động cảnh báo người dùng

mà không yêu cầu thao tác thủ công liên tục.

---

# 2. CÁC NĂNG LỰC CỐT LÕI

Hệ thống AAA cung cấp 4 nhóm năng lực chức năng chính, tạo nên một chu trình khép kín từ khâu tiếp nhận yêu cầu đến thực thi tự động.

---

## 2.1. Tương tác Ngôn ngữ Tự nhiên (NLP Chat)

AAA hỗ trợ giao tiếp thông qua hội thoại tự nhiên, cho phép người dùng điều khiển hệ thống như một trợ lý thực thụ.

### Khả năng

- Hiểu ngữ cảnh liên tục
- Phân tích ý định người dùng
- Xử lý câu lệnh phức tạp nhiều bước
- Duy trì trạng thái hội thoại

### Ví dụ ứng dụng

> “Kiểm tra email mới từ giảng viên. Nếu có lịch họp mới thì thêm vào Calendar và nhắc tôi trước deadline 2 tiếng.”

---

## 2.2. Trích xuất Dữ liệu Ngầm (Background Ingestion)

Hệ thống có khả năng hoạt động nền (**background processing**) để liên tục cập nhật thông tin mà không yêu cầu người dùng phải chủ động mở ứng dụng.

### Khả năng

- Tự động quét email định kỳ
- Phân tích nội dung thông báo hệ thống
- Trích xuất dữ liệu mang tính ngữ nghĩa quan trọng

### Ví dụ ứng dụng

- Tự động nhận diện deadline assignment từ hệ thống học tập
- Phân tích email thông báo thay đổi lịch thi hoặc lịch họp

---

## 2.3. Đồng bộ Tự trị (Autonomous Sync)

Dựa trên ngữ cảnh đã phân tích từ các luồng dữ liệu ngầm, AAA tự động đưa ra quyết định hành động nhằm thống nhất thông tin cá nhân.

### Khả năng

- Ra quyết định tự trị
- Đồng bộ dữ liệu vào hệ thống Local
- Tự động cập nhật lịch trình

### Ví dụ ứng dụng

- Tự động tạo Event vào Lịch nội bộ (In-app Calendar) khi phát hiện lịch họp mới
- Đồng bộ deadline dự án vào công cụ quản lý công việc cục bộ

---

## 2.4. Cảnh báo Chủ động (Proactive Notification)

AAA hoạt động như một hệ thống radar cá nhân, kịp thời thu hút sự chú ý của người dùng vào những thời điểm quan trọng.

### Khả năng

- Gửi thông báo trực tiếp tới hệ điều hành
- Native OS Notification
- System Tray Alert

### Ví dụ ứng dụng

- Bật cảnh báo Pop-up khi có email ưu tiên cao (VIP)
- Nhắc nhở tự động khi sắp đến hạn chót (Deadline)

---

# 3. CÁCH TIẾP CẬN CÔNG NGHỆ (LOCAL-FIRST HYBRID ARCHITECTURE)

Để đáp ứng các yêu cầu:

- Chạy ngầm liên tục
- Phản hồi thời gian thực
- Tiêu thụ tối thiểu tài nguyên
- Bảo vệ quyền riêng tư tuyệt đối

AAA áp dụng mô hình kiến trúc lai (**Hybrid Architecture**) kết hợp sức mạnh của nhiều hệ sinh thái.

---

## 3.1. Vỏ Giao diện Siêu nhẹ (Presentation Layer)

Frontend được xây dựng bằng kiến trúc:

- **Tauri**
- **React**
- **GSAP**

### Tauri (Rust Core)

Sử dụng Native WebView và Rust Runtime thay vì đóng gói Chromium cồng kềnh như Electron.

### Lợi ích

- Tiêu thụ RAM cực thấp
- Khởi động tức thời
- Kích thước file cài đặt nhỏ gọn
- Quản lý System Tray mượt mà

### React & GSAP

- React quản lý trạng thái hội thoại
- GSAP xử lý hiệu ứng chuyển động
- Cung cấp phản hồi thị giác trực quan về trạng thái suy luận của AI Agent

---

## 3.2. Lõi AI Tự trị & Suy giảm Có kiểm soát (Python Sidecar & Graceful Degradation)

Backend không phụ thuộc vào máy chủ trung tâm mà vận hành 100% dưới dạng một tiến trình song song (**Sidecar Process**) trên máy người dùng bằng hệ sinh thái Python, với khả năng ứng biến linh hoạt theo trạng thái kết nối mạng.

---

### Bảo vệ Dữ liệu Cục bộ (Local-first Database)

Toàn bộ:

- Lịch sử ngữ cảnh
- Dữ liệu email nhạy cảm

được lưu trữ trực tiếp bằng SQLite trên ổ cứng thiết bị.

Điều này đảm bảo:

- Quyền riêng tư tuyệt đối
- Không phụ thuộc hạ tầng cloud
- Dữ liệu được cô lập hoàn toàn phía client

---

### Xử lý Ngầm Bất đồng bộ (Async Ingestion)

Hệ thống sử dụng `asyncio` để quản lý các luồng cào dữ liệu ngầm trên cùng một tiến trình.

### Mục tiêu

- Ứng dụng luôn phản hồi nhanh
- Không nghẽn luồng giao diện chính
- Hỗ trợ realtime background ingestion

---

### Chế độ Đám mây & Local LLM (Hybrid Inference)

Kiến trúc **Hybrid LLM Adapter** cho phép kết nối linh hoạt tới nhiều nhà cung cấp AI:

- Cloud API: OpenAI, Gemini
- Local LLM: Llama 3 (thông qua Ollama)

### Vai trò của Custom ReAct Agent

Thay vì sử dụng các thư viện cồng kềnh như LangChain, AAA sử dụng kiến trúc **Custom ReAct Agent** được thiết kế gọn nhẹ, tối ưu hóa đặc biệt cho mục đích:

- Điều phối AI Agent cực kỳ nhanh và tiêu tốn ít tài nguyên.
- Chuẩn hóa structured output (JSON).
- Giảm rủi ro Hallucination bằng các prompt template khắt khe.
- Biến AI thành hệ thống có tính xác định cao.

---

### Chế độ Lệnh tĩnh Ngoại tuyến (Rule-Based Fallback)

AAA áp dụng nguyên lý:

# Graceful Degradation

Khi mất mạng hoặc API bị gián đoạn:

- Ứng dụng không bị treo
- Không ngắt trải nghiệm người dùng
- Không yêu cầu local AI model nặng

### Cơ chế hoạt động

Hệ thống tự động chuyển sang:

- Regex-based parsing
- Static command execution

Người dùng tương tác bằng các lệnh tĩnh như:

```bash
/calendar
/note
```