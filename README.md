# Autonomous AI Assistant (AAA)

Dự án Trợ lý AI Đa nền tảng (Desktop & Web) được xây dựng trên kiến trúc **Clean Architecture** và **Feature-Sliced Design**. Đây là một trợ lý thông minh có khả năng tư duy tự trị với lõi **Custom ReAct Agent** tối ưu, khả năng ghi nhớ dài hạn, và đặc biệt là hệ thống **Cảnh báo Chủ động (Proactive Alerts)** chạy hoàn toàn ngầm.

---

## ✨ Các Tính năng Nổi bật

- 🧠 **Custom ReAct Agent**: Tự chủ phân tích ý định, suy luận và gọi Tool linh hoạt, không phụ thuộc vào các framework cồng kềnh như LangChain.
- 🔄 **Hybrid LLM Fallback**: Chuyển đổi mượt mà giữa Cloud LLM (OpenAI/Gemini) và Local LLM (Ollama/Llama 3). Đảm bảo bảo mật 100% dữ liệu và hoạt động ngay cả khi rớt mạng.
- 🔔 **Background Ingestion & Proactive Alerts**: Hệ thống Worker chạy ngầm định kỳ quét Email và Lịch nội bộ (In-app Calendar). Cảnh báo sự kiện sắp diễn ra (trước 5 phút) hoặc Email Khẩn/VIP ngay lập tức qua Toast Notification mà không cần người dùng tương tác.

---

## 🏗 Kiến trúc Thư mục

### Backend (Python + FastAPI)
Kiến trúc Microkernel mở rộng linh hoạt:
- `backend/domain/`: Chứa các Entity cốt lõi, Base Events, và Interface. 
- `backend/application/`: Chứa Use Cases (AgentCore, AlertEngine), DTOs và các Rules cảnh báo.
- `backend/infrastructure/`: Chứa LLM Adapters (Hybrid), Plugins (Email, Calendar), Workers (APScheduler) và EventBus (Central Hub).
- `backend/presentation/`: Tầng giao tiếp với FastAPI Routers và WebSocket Handlers.

### Frontend (React + TypeScript + Tauri)
Frontend tuân thủ tiêu chuẩn Modular/Feature-Driven Design:
- `frontend/src-tauri/`: Code Rust Native quản lý cửa sổ Desktop (System Tray, Shortcuts, Overlays).
- `frontend/src/core/`: Chứa Global State (Zustand) và Type Schemas (Zod).
- `frontend/src/features/`: Chứa các phân hệ độc lập (Auth, Chat, Settings).

---

## 🚀 Hướng dẫn Thiết lập Môi trường

### 1. Cấu hình Biến Môi trường (.env)
Tại thư mục `backend/`, sửa/đổi tên file `.env.example` thành `.env` với các nội dung sau:
```env
# Khóa bí mật dùng để mã hoá dữ liệu trong CSDL
DB_ENCRYPTION_KEY=0123456789abcdef0123456789abcdef
# Khóa bí mật để ký JWT Token cho phiên đăng nhập
JWT_SECRET_KEY=your_super_secret_jwt_key_here
```

### 2. Cấu hình Local LLM (Ollama)
AAA hỗ trợ mô hình LLM chạy cục bộ:
1. Tải và cài đặt **[Ollama](https://ollama.com/)**.
2. Kéo mô hình bạn muốn dùng (Ví dụ: `ollama run llama3`).
3. Đảm bảo server Ollama đang chạy ở port `11434`.
4. Trong Settings UI của App, cấu hình URL là `http://localhost:11434` và chọn Provider là Ollama.

*(Nếu dùng API của OpenAI hay Gemini, bạn có thể nhập API Key trực tiếp trong phần Settings).*

### 3. Cấu hình Plugin (OAuth)
- Hệ thống hỗ trợ đọc Email qua Gmail API. Hãy đặt file `credentials.json` lấy từ Google Cloud Console vào thư mục `backend/`.
- Mở AAA, vào phần **Settings > Plugins** để cấp quyền.

---

## 🛠 Hướng dẫn Khởi chạy (Môi trường Dev)

### 1. Backend (FastAPI)
Yêu cầu: Python 3.10+

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate   # Windows
# source venv/bin/activate  # macOS/Linux

# Cài đặt thư viện
pip install -r requirements.txt

# Khởi chạy Server (QUAN TRỌNG: Phải đứng ở thư mục gốc AI-Assistant)
cd ..

# (Tùy chọn) Khởi tạo dữ liệu mẫu (Seeding Database)
# Chạy lệnh sau để tạo sẵn tài khoản (Username: master_admin / Password: password)
python scripts/seed.py

python -m uvicorn backend.main:app --reload
```

### 2. Frontend (Web/Desktop)
Yêu cầu: Node.js 18+ và Rust (Nếu build Desktop).

```bash
cd frontend
npm install

# Chạy Web Mode (Mở http://localhost:5173)
npm run dev

# Chạy Desktop Mode (Khởi chạy bằng Tauri)
npm run tauri dev
```

---

## 📦 Kiến trúc Production (Tauri Sidecar)
Khi phân phối, toàn bộ Backend Python sẽ được đóng gói bằng **PyInstaller** thành một file thực thi độc lập và nhúng vào Desktop app qua tính năng **Tauri Sidecar**.

### 🚀 Hướng Dẫn Build Production (Tạo File Cài Đặt)

**Bước 1: Nén Backend Python thành File Thực Thi (Sidecar)**
Tại thư mục gốc của dự án, chạy Script PowerShell:
```powershell
# Chạy với quyền ExecutionPolicy Bypass nếu hệ thống chặn script
powershell -ExecutionPolicy Bypass -File .\scripts\build_sidecar.ps1
```

**Bước 2: Biên Dịch Giao Diện và Đóng Gói Desktop App**
```bash
cd frontend
npm run tauri build
```

**Kết quả (Files đầu ra):**
Sau khi hoàn tất quá trình build, bạn sẽ nhận được 2 thành phần chính:
1. **File thực thi Backend (Sidecar):** Nằm tại `frontend/src-tauri/bin/backend-x86_64-pc-windows-msvc.exe`. File này đã được đóng gói nhúng sẵn Python và toàn bộ thư viện.
2. **File cài đặt App (Installer):** Nằm tại `frontend/src-tauri/target/release/bundle/nsis/` (file `.exe`) hoặc `msi/` (file `.msi`). Đây là file cài đặt hoàn chỉnh dùng để phân phối cho người dùng cuối.

---

## 🧪 Hướng dẫn & Kịch bản Kiểm thử Thực tế (E2E Testing Scenarios)

Phần này cung cấp các kịch bản kiểm thử (Test Cases) rõ ràng, từng bước một (Step-by-step) để bạn hoặc Tester có thể nghiệm thu ứng dụng một cách dễ dàng, bao gồm cả các tính năng ẩn chạy ngầm.

### Kịch bản 1: Kiểm thử Khả năng Ghi nhớ (Memory & Core AI)
*Mục đích: Đảm bảo AI biết sử dụng Tool `memory_plugin` để lưu thông tin và truy xuất lại ở tương lai.*
- **Bước 1 (Chuẩn bị):** Vào Cài đặt > Tiện ích mở rộng. Đảm bảo "Bộ nhớ AI" đã được BẬT.
- **Bước 2 (Ghi nhớ):** Mở cửa sổ Chat, nhập prompt: 
  > *"Sở thích của tôi là lập trình Python và tôi rất ghét ăn hành tây, hãy nhớ điều này nhé."*
- **Bước 3 (Kiểm tra):** Đợi AI trả lời xác nhận. Bấm vào nút "Cuộc trò chuyện mới" (Tạo session mới hoàn toàn).
- **Bước 4 (Truy vấn):** Nhập prompt: 
  > *"Bạn có biết tôi ghét ăn món gì không?"*
- **Kết quả kỳ vọng:** AI phải gọi tool tìm kiếm trong Vector DB và trả lời chính xác là bạn ghét ăn hành tây, mặc dù đây là một cuộc hội thoại hoàn toàn mới.

### Kịch bản 2: Kiểm thử Quản lý Lịch trình (Calendar Plugin)
*Mục đích: Đảm bảo AI hiểu định dạng thời gian thực tế và gọi đúng hàm cập nhật Database.*
- **Bước 1:** Bật tiện ích "Lịch" trong Cài đặt.
- **Bước 2 (Tạo sự kiện):** Nhập prompt:
  > *"Hãy tạo một sự kiện có tên là 'Họp với sếp' vào lúc 3 giờ chiều ngày mai."*
- **Bước 3 (Truy vấn):** Mở tab **Lịch trình** trên thanh điều hướng bên trái. 
- **Kết quả kỳ vọng:** Bạn sẽ nhìn thấy sự kiện "Họp với sếp" xuất hiện ngay lập tức trên lịch tại đúng khung giờ ngày mai mà không cần tải lại trang.

### Kịch bản 3: Kiểm thử Đọc Email (OAuth Integration)
*Mục đích: Kiểm tra kết nối Google OAuth và khả năng đọc dữ liệu từ Gmail.*
- **Bước 1:** Đảm bảo file `credentials.json` đã có sẵn, vào Cài đặt > Tiện ích > Bật "Email" và bấm "Cấu hình" để cấp quyền Google.
- **Bước 2:** Nhập prompt vào Chat:
  > *"Hãy kiểm tra hộp thư của tôi xem có 3 email nào mới nhất không, và tóm tắt chúng lại."*
- **Kết quả kỳ vọng:** AI gọi tool đọc email, hiển thị danh sách 3 email mới nhất từ tài khoản thật của bạn và tóm tắt nội dung chính. Nếu chưa cấp quyền, AI phải phản hồi: *"Vui lòng vào Cài đặt để cấp quyền cho phép truy cập Gmail"*.

### Kịch bản 4: Kiểm thử Tự động Đồng bộ Lịch từ Email (Autonomous Sync)
*Mục đích: Đảm bảo khi có email nhắc nhở lịch trình gửi đến hộp thư, hệ thống tự động đọc ngầm, phát hiện lịch và ghi vào DB (Calendar) mà không cần bạn thao tác.*
- **Bước 1 (Chuẩn bị):** Bạn dùng điện thoại hoặc một email khác, gửi một email đến địa chỉ Gmail đã liên kết với tiêu đề: *"Lịch Phỏng Vấn AI Engineer"* và nội dung: *"Chào bạn, lịch phỏng vấn của bạn sẽ diễn ra vào 9h00 sáng ngày mai. Vui lòng tham gia đúng giờ"*. 
- **Bước 2 (Mô phỏng):** Giữ nguyên ứng dụng AI không làm gì (để nguyên đó). Hệ thống Email Scanner sẽ chạy ngầm mỗi 60 giây.
- **Bước 3 (Kiểm tra):** Tầm 1 phút sau, hệ thống sẽ nảy một Toast Notification thông báo: *"Đã tự động thêm sự kiện 'Phỏng vấn AI Engineer' vào lịch"*.
- **Kết quả kỳ vọng:** Bạn mở tab **Lịch trình** sẽ thấy một sự kiện mới toanh vừa được tạo thành công cho lúc 9h sáng ngày mai.

### Kịch bản 5: Kiểm thử Tính năng Cảnh báo Chạy ngầm (Background Proactive Alerts)
*Mục đích: Nghiệm thu hệ thống Background Worker tự động gửi thông báo (Toast/Notification) mà không cần người dùng hỏi.*
- **Bước 1 (Chuẩn bị dữ liệu):** Mở màn hình Chat, yêu cầu AI tạo một sự kiện sắp diễn ra:
  > *"Hãy tạo sự kiện 'Test thông báo ngầm' diễn ra vào thời điểm 5 phút nữa kể từ bây giờ."*
- **Bước 2 (Mô phỏng chạy ngầm):** Thu nhỏ cửa sổ ứng dụng (Minimize) hoặc chuyển sang Tab khác (Ví dụ: Tab Cài đặt) và **KHÔNG LÀM GÌ CẢ**.
- **Bước 3 (Chờ đợi):** Đợi hệ thống đếm ngược. APScheduler chạy ngầm sẽ quét database mỗi 60 giây.
- **Kết quả kỳ vọng:** Khi thời gian hiện tại chạm mốc **trước 5 phút** so với giờ sự kiện diễn ra, một thông báo Toast màu đỏ/vàng sẽ tự động nảy lên trên màn hình với nội dung: *"Sự kiện 'Test thông báo ngầm' sắp diễn ra"*, đồng thời bộ đếm ở tab "Thông báo" sẽ tăng lên +1.

### Kịch bản 6: Kiểm thử Kháng lỗi & Hoạt động Ngoại tuyến (Offline Fallback)
*Mục đích: Đảm bảo khi mất mạng, hệ thống vẫn hoạt động bằng Local LLM (Ollama).*
- **Bước 1:** Đảm bảo bạn đang sử dụng API Key (OpenAI/Gemini) và mạng Internet đang hoạt động bình thường. Hỏi một câu bất kỳ để đảm bảo AI Cloud đang trả lời.
- **Bước 2 (Ngắt kết nối):** Rút cáp mạng hoặc tắt Wi-Fi của máy tính.
- **Bước 3:** Nhập prompt:
  > *"Thời tiết hôm nay thế nào?"*
- **Kết quả kỳ vọng:** Hệ thống không văng lỗi Đứt Mạng (Crash). Nó tự động nhận diện mất kết nối Cloud, bắt HTTP Timeout, chuyển hướng truy vấn xuống Ollama Local. AI sẽ phản hồi (dù có thể chậm hơn) và tự biết từ chối trả lời về thời tiết do đang offline, nhưng vẫn có thể chat các chủ đề thông thường. Đảm bảo UI không hiển thị màn hình trắng.

### Kịch bản 7: Kiểm thử Giao diện Tạo thủ công (Offline UI / Manual Entry)
*Mục đích: Đảm bảo người dùng có thể thêm Sự kiện và Công việc thủ công bằng Form giao diện truyền thống mà không cần dùng đến AI.*
- **Bước 1 (Tạo Công việc):** Chuyển sang tab **Công việc** ở thanh điều hướng bên trái, bấm nút **"Tạo mới"**. 
- **Bước 2:** Một hộp thoại (Modal) sẽ hiện ra. Điền Tên công việc (VD: "Mua sắm cuối tuần") và bấm "Lưu công việc".
- **Bước 3 (Kiểm tra Task):** Form sẽ tự động đóng lại, công việc "Mua sắm cuối tuần" xuất hiện ngay lập tức ở danh sách Task.
- **Bước 4 (Tạo Sự kiện):** Chuyển sang tab **Lịch trình**, bấm nút **"Tạo sự kiện"**.
- **Bước 5 (Kiểm tra Event):** Điền Tên sự kiện, thời gian Bắt đầu và Kết thúc rồi bấm Lưu. Sự kiện sẽ hiển thị ngay lập tức trên giao diện.
- **Kết quả kỳ vọng:** Toàn bộ quá trình tạo mới diễn ra cực kỳ nhanh (instant), không có loading AI, không tốn Token và hoạt động trơn tru ngay cả khi không có kết nối internet để gọi AI.
