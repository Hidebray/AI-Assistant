# Autonomous AI Assistant (AAA)

Dự án Trợ lý AI Đa nền tảng (Desktop & Web) được xây dựng trên kiến trúc **Clean Architecture** và **Feature-Sliced Design**. Đây là một trợ lý thông minh có khả năng tư duy tự trị với lõi **Custom ReAct Agent** tối ưu, khả năng ghi nhớ dài hạn, và đặc biệt là hệ thống **Cảnh báo Chủ động (Proactive Alerts)** chạy hoàn toàn ngầm.

---

## ✨ Các Tính năng Nổi bật

- 🧠 **Custom ReAct Agent**: Tự chủ phân tích ý định, suy luận và gọi Tool linh hoạt, không phụ thuộc vào các framework cồng kềnh như LangChain.
- 🔄 **Hybrid LLM Fallback**: Chuyển đổi mượt mà giữa Cloud LLM (OpenAI/Gemini) và Local LLM (Ollama/Llama 3). Đảm bảo bảo mật 100% dữ liệu và hoạt động ngay cả khi rớt mạng.
- ⚡ **Graceful Degradation (Offline Commands)**: Hỗ trợ các lệnh tĩnh bằng Regex (`/lich`, `/note`, `/task`) khi hoàn toàn ngoại tuyến.
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

## 🧪 Luồng Nghiệp vụ & Kịch bản Kiểm thử (Business Flows & Scenarios)

Phần này tài liệu hóa chi tiết toàn bộ tính năng, luồng nghiệp vụ (Business flows), trường hợp sử dụng (Use cases), các tình huống ngoại lệ (Edge cases) và quy tắc nghiệp vụ (Business rules) cốt lõi của hệ thống AAA.

### 1. Trợ lý AI Cốt lõi & Quản lý Bộ nhớ (Core AI & Memory Management)
**Luồng nghiệp vụ (Business Flow):**
1. Người dùng gửi tin nhắn Prompt.
2. Custom ReAct Agent phân tích ý định và trích xuất từ khóa.
3. Query Vector DB để lấy ngữ cảnh (trí nhớ dài hạn) có liên quan.
4. Agent suy luận (Chain of Thought) để quyết định chuỗi công cụ (Tools) cần gọi.
5. Thực thi Tools, thu thập kết quả, tổng hợp câu trả lời tự nhiên và trả về UI.

**Trường hợp sử dụng (Use Cases):**
- **Ghi nhớ thông tin cá nhân:** Người dùng nói *"Sở thích của tôi là lập trình Python, hãy nhớ điều này"*. AI gọi Tool ghi nhớ. Trong hội thoại mới, khi hỏi *"Tôi thích ngôn ngữ nào?"*, AI truy xuất thành công từ Vector DB và trả lời.
- **Tra cứu và lưu trữ liên hợp:** Kết hợp Tìm kiếm Web để lấy thông tin mới (VD: giá vàng hôm nay), sau đó lưu trực tiếp vào bộ nhớ theo yêu cầu.

**Tình huống ngoại lệ (Edge Cases):**
- **Công cụ bị lỗi ngẫu nhiên (Flaky Tool):** API trả về lỗi Timeout hoặc HTTP 500. Agent không báo lỗi ngay mà tự động phân tích lý do, thực hiện retry (gọi lại) hoặc fallback sang hướng tiếp cận khác.
- **Tràn bộ nhớ ngữ cảnh (Context Overflow):** Lịch sử hội thoại vượt ngưỡng an toàn (ví dụ: > 3000 tokens). Backend tự kích hoạt luồng xử lý ngầm để tóm tắt các hội thoại cũ thành một `system_summary` ngắn gọn, giúp duy trì trò chuyện vô hạn mà không gặp lỗi Token Limit.

**Quy tắc nghiệp vụ (Business Rules):**
- **Quyền riêng tư:** AI không được phép tự phán đoán hoặc bịa đặt (hallucinate) thông tin cá nhân. Nếu không tìm thấy trong DB, phải trả lời là không biết.
- **Phân quyền Tool:** Chỉ các công cụ được bật (`Enable`) trong bảng Cài đặt Tiện ích mới được đưa vào Context Prompt của Agent.

---

### 2. Hệ thống Cảnh báo Chủ động chạy ngầm (Proactive Alerts)
**Luồng nghiệp vụ (Business Flow):**
1. Background Worker (APScheduler) chạy độc lập với giao diện mỗi `X` giây.
2. Worker truy vấn DB (Lịch, Task) và kết nối API ngoài (Gmail) để lấy dữ liệu mới.
3. Đưa dữ liệu qua Alert Engine để đánh giá theo bộ Rules (Quy tắc).
4. Nếu thoả mãn, Alert Engine đẩy sự kiện qua Central EventBus.
5. WebSocket Server nhận sự kiện và gửi tín hiệu về Frontend (Tauri).
6. UI hiển thị System Toast / Notification khẩn cấp.

**Trường hợp sử dụng (Use Cases):**
- **Nhắc nhở lịch trình:** Thông báo *"Cuộc họp hàng ngày sắp diễn ra"* tự động nảy lên màn hình trước thời điểm diễn ra sự kiện 5 phút.
- **Báo cáo Email quan trọng:** Quét thấy email từ sếp hoặc email có tag "Khẩn", ứng dụng tự báo động ngay lập tức kể cả khi bạn không mở app.

**Tình huống ngoại lệ (Edge Cases):**
- **Trạng thái ẩn (Minimized/System Tray):** Ứng dụng không ở cửa sổ chính (Active Window), cảnh báo vẫn phải được kích hoạt thông qua Native OS Notification (Windows Toast/macOS Notification).
- **Trùng lặp sự kiện (Spam Alerts):** Quá nhiều sự kiện cùng lúc dẫn đến spam thông báo. Hệ thống xử lý qua hàng đợi Queue và cơ chế Debounce.

**Quy tắc nghiệp vụ (Business Rules):**
- **Idempotency (Tính luỹ đẳng):** Một sự kiện cụ thể chỉ được phép kích hoạt cảnh báo đúng 1 lần. Trạng thái `is_alerted` phải được cập nhật ngay vào DB.
- **Điều kiện kích hoạt Email:** Chỉ áp dụng cho các email có trạng thái "Chưa đọc" (Unread).

---

### 3. Cơ chế Kháng lỗi & Hoạt động Ngoại tuyến (Resiliency & Offline Fallback)
**Luồng nghiệp vụ (Business Flow):**
1. Yêu cầu AI được gửi tới Backend. Network Interceptor kiểm tra tình trạng kết nối mạng.
2. Nếu gọi Cloud API (OpenAI/Gemini) thất bại do đứt mạng, ném ra Network Exception.
3. `HybridFallbackAdapter` bắt lỗi, tự động định tuyến lại prompt xuống Local LLM (Ollama/Llama 3).
4. Nếu Ollama cũng không khả dụng (chưa bật), chuyển xuống Fallback Tầng 2 (Graceful Degradation).

**Trường hợp sử dụng (Use Cases):**
- **Chuyển đổi liền mạch (Seamless Fallback):** Rớt mạng khi đang chat. Trợ lý tự chuyển qua chạy LLM nội bộ. Thời gian phản hồi có thể chậm hơn nhưng logic câu trả lời vẫn đúng, không hiện lỗi đứt mạng.

**Tình huống ngoại lệ (Edge Cases):**
- **Offline Toàn phần (Total Offline):** Mất cả mạng Internet lẫn Local LLM. Ứng dụng vào chế độ Graceful Degradation. Người dùng gõ lệnh tĩnh như `/calendar`, `/task`. Hệ thống Parse Regex trực tiếp trên Frontend/Backend và render UI tĩnh.

**Quy tắc nghiệp vụ (Business Rules):**
- **Độ ưu tiên xử lý:** Cloud LLM (Cao nhất) -> Local LLM (Trung bình) -> Regex Commands (Dự phòng cuối).
- **Đồng bộ hóa (Syncing):** Khi có mạng trở lại, mọi thay đổi tạo ra trong lúc Offline (như tạo Task qua lệnh tĩnh) phải được đồng bộ hóa hoàn chỉnh.

---

### 4. Năng lực Quản lý Đa tiện ích (Tooling & Integration)
**Luồng nghiệp vụ (Business Flow):**
1. Nhận ý định thao tác với ứng dụng bên thứ 3 hoặc module nội bộ từ người dùng.
2. Agent tạo bộ tham số (Parameters Schema) tương ứng.
3. Validate tham số bằng Pydantic. Nếu hợp lệ -> Gọi API/DB.
4. Trả kết quả cập nhật về cho UI. Nếu UI đang mở tab tương ứng (VD: Tab Lịch), phát tín hiệu WebSocket để reload Data ngay lập tức.

**Trường hợp sử dụng (Use Cases):**
- **Lịch & Sự kiện:** *"Tạo một sự kiện ăn trưa vào ngày mai lúc 12h"*. AI trích xuất thời gian, tạo bản ghi.
- **Quản lý Task:** *"Thêm việc mua sắm, sau đó hiển thị toàn bộ task hiện có"*. AI gọi tool `create_task`, tiếp tục gọi tool `list_tasks` và trình bày.
- **Email:** *"Gửi một email tới khachhang@gmail.com để cảm ơn"*. Hệ thống cấu trúc nội dung, tạo draft, hoặc gửi ngay nếu được phép.

**Tình huống ngoại lệ (Edge Cases):**
- **Thiếu thông tin (Missing Arguments):** Người dùng bảo *"Tạo lịch cuộc họp"* nhưng thiếu ngày giờ. Trợ lý KHÔNG được tự ý đoán ngày (trừ khi có từ khóa "hôm nay", "ngày mai"). Trợ lý phải trả về prompt hỏi: *"Bạn muốn đặt cuộc họp vào thời gian nào?"*.
- **Chưa uỷ quyền (Unauthorized/Missing OAuth):** Gọi tool Email nhưng chưa liên kết Gmail. Agent bắt lỗi trả về từ Plugin, thông báo lại cho người dùng: *"Vui lòng vào Cài đặt để cấp quyền cho phép truy cập Gmail trước khi thực hiện thao tác này"*.

**Quy tắc nghiệp vụ (Business Rules):**
- **Xác thực phá huỷ (Destructive Actions):** Các thao tác xóa (Xóa toàn bộ lịch, Xóa Task quan trọng) nên được AI yêu cầu người dùng xác nhận lại trước khi thực thi.
- **Bảo mật OAuth:** Token truy cập từ bên thứ 3 (Gmail API) phải được lưu trữ mã hóa và không bao giờ xuất hiện trong log của AI hay terminal.
