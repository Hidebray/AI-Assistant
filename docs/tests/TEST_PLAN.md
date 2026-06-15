# Master Test Plan: Autonomous AI Assistant (AAA)

## 1. Testing Scope

### In Scope
Tài liệu này bao phủ việc kiểm thử cho các tính năng cốt lõi của hệ thống AAA dựa trên kiến trúc Local-first Hybrid:
1. **Giao tiếp Ngôn ngữ Tự nhiên (NLP Chat)**: Phân tích ý định, duy trì ngữ cảnh, gọi Plugin (Tools) tự động qua Custom ReAct Agent.
2. **Cảnh báo Email Ngầm (Email Scanner Alerts)**: Chức năng Background Ingestion định kỳ quét email và kích hoạt AlertEngine cho các luồng thư khẩn/VIP.
3. **Lịch nội bộ & Nhắc nhở (In-app Calendar)**: Quản lý lịch trình, tạo event và trigger cảnh báo qua websocket/toast 5 phút trước khi sự kiện bắt đầu.
4. **Hybrid LLM Fallback**: Khả năng suy luận linh hoạt giữa Cloud LLM (OpenAI/Gemini) và Local LLM (Ollama/Llama 3) khi trạng thái mạng hoặc cấu hình API Key thay đổi.

6. **Cài đặt & Quản lý Plugin (Settings & Plugins)**: Bật/tắt Plugin, điền API Keys, quản lý quyền hệ thống.

### Out of Scope
- Kiểm thử sâu về UI/UX Frontend (màu sắc, khoảng cách pixel, độ mượt của CSS animation) không ảnh hưởng tới luồng nghiệp vụ.
- Kiểm thử cài đặt Desktop Application / Tauri packaging (chỉ tập trung vào business logic đang chạy trên Web Browser/Vite hiện tại).
- Penetration Testing chuyên sâu về hạ tầng mạng (ngoài phạm vi bảo vệ Local DB).
- Độ chính xác tuyệt đối của mô hình AI (phụ thuộc vào nhà cung cấp API, hệ thống chỉ test khả năng parse và điều hướng prompt).

---

## 2. Testing Strategy

Chiến lược kiểm thử AAA được phân lớp theo mô hình Kim tự tháp (Testing Pyramid), bao gồm:

### Unit Testing
- **Mục tiêu**: Kiểm chứng tính đúng đắn của từng module nhỏ lẻ biệt lập (ví dụ: các Alert Rules của AlertEngine).
- **Thực hiện**: Mock các đối tượng phức tạp như Database Session, LLM API, EventBus. 

### Integration Testing
- **Mục tiêu**: Đảm bảo các luồng giao tiếp giữa các thành phần liền kề hoạt động mượt mà. 
- **Trọng điểm**: Giao tiếp giữa EventBus và Websocket (Chat), giao tiếp giữa Worker (Calendar/Email) và AlertEngine, kết nối giữa HybridLLMAdapter và Ollama/OpenAI.

### System Testing
- **Mục tiêu**: Xác thực toàn bộ hệ thống (Frontend + Backend + SQLite + LLM API) hoạt động đúng như đặc tả từ góc độ người dùng (End-to-End).
- **Trọng điểm**: Toàn bộ vòng đời của một tin nhắn từ UI -> Websocket -> AgentCore -> LLM -> ToolExecutor -> Database -> UI.

### User Acceptance Testing (UAT)
- **Mục tiêu**: Người dùng cuối (hoặc Beta Testers) đánh giá tính tiện dụng, thời gian phản hồi thực tế của AI và sự hữu ích của các cảnh báo.

---

## 3. Testing Techniques

Các kỹ thuật kiểm thử sau sẽ được kết hợp áp dụng để tối đa hóa độ bao phủ:

### Functional Testing
- **Mục đích**: Xác nhận các chức năng hoạt động đúng logic nghiệp vụ (VD: Lệnh `/calendar` trả về đúng sự kiện ngày mai).
- **Phạm vi áp dụng**: 100% In-scope features.
- **Đối tượng**: API endpoints, Agent workflow, Plugin execution.

### Boundary Value Analysis
- **Mục đích**: Tìm lỗi tại các vùng ranh giới giới hạn.
- **Phạm vi áp dụng**: Số lượng email quét (giới hạn 5), khoảng thời gian cảnh báo (đúng 5 phút trước giờ diễn ra), độ dài cực lớn của tin nhắn.
- **Đối tượng**: EmailScannerWorker, CalendarNotifierWorker, Chat Input.

### Equivalence Partitioning
- **Mục đích**: Giảm thiểu số lượng test case bằng cách chia dữ liệu đầu vào thành các nhóm tương đương.
- **Phạm vi áp dụng**: Input của Regex Commands, phân loại mức độ khẩn cấp email (VIP, Khẩn cấp, Bình thường).
- **Đối tượng**: Alert Rules.

### Negative Testing
- **Mục đích**: Kiểm tra cách hệ thống xử lý các thao tác bất thường hoặc dữ liệu sai.
- **Phạm vi áp dụng**: Nhập API key sai, AI trả về JSON rác, mất mạng giữa chừng, cấp thiếu quyền cho plugin.
- **Đối tượng**: LLM Factory, ToolExecutor, Settings UI.

### Regression Testing
- **Mục đích**: Đảm bảo code mới không làm hỏng tính năng cũ.
- **Phạm vi áp dụng**: Toàn hệ thống, đặc biệt là EventBus vì nó là trục trung tâm (Central Hub) định tuyến mọi event.
- **Đối tượng**: Toàn bộ System Tests.

### Security Testing
- **Mục đích**: Đảm bảo API Keys và dữ liệu nhạy cảm được bảo vệ an toàn trên Local DB.
- **Phạm vi áp dụng**: Chức năng lưu và mã hóa thông số Settings (`encryption.py`), cơ chế xác thực token.
- **Đối tượng**: Local SQLite (bảng user_settings).

### Performance Testing
- **Mục đích**: Xác định giới hạn chịu tải khi chạy trên máy cá nhân có cấu hình yếu.
- **Phạm vi áp dụng**: Concurrent Background Workers, streaming response time từ Local Llama 3.
- **Đối tượng**: AsyncEventBus, HybridLLMAdapter, APScheduler.

---

## 4. Entry Criteria
- Mã nguồn đã được dev review và deploy/run thành công trên môi trường Test (Local localhost:5173 và 8000).
- Hệ thống SQLite đã chạy migration đầy đủ.
- Môi trường thử nghiệm có đầy đủ cấu hình mạng mô phỏng (bật/tắt internet) và có cài đặt sẵn Ollama + Llama3 model.
- Test Cases đã được phê duyệt bởi Product Owner/Stakeholders.

## 5. Exit Criteria
- 100% các Test Cases mức độ Critical và High đều PASS.
- Mọi bugs cấp độ 1 và 2 (Blocker/Critical) đã được giải quyết.
- Có không quá 3 bugs mức độ Low/Medium tồn đọng (được đưa vào backlog).
- Tính năng chạy trơn tru trên trình duyệt mô phỏng.
- Toàn bộ Test Cases được cập nhật Actual Output và Result.
