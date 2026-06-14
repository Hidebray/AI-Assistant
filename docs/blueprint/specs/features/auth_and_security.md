# Đặc tả Nghiệp vụ Xác thực & Bảo mật (Auth & Security Specs)

Tài liệu này đặc tả các luồng nghiệp vụ và quy tắc bảo mật nội bộ cho dự án Autonomous AI Assistant (AAA). Áp dụng triết lý **Local-First**, toàn bộ quá trình xác thực và lưu trữ dữ liệu diễn ra hoàn toàn trên thiết bị vật lý của người dùng, tuyệt đối không phụ thuộc vào bất kỳ Cloud Server trung tâm nào.

---

## 1. User Stories (Câu Chuyện Người Dùng)

- **US01 (Đăng ký Khởi tạo)**: *Là một người dùng mới (New User)*, tôi muốn thiết lập một tài khoản cục bộ (Master User) kèm mật khẩu an toàn, *để* đảm bảo không ai khác dùng chung máy tính vật lý này có thể xem được lịch sử chat cá nhân và tài liệu mật của tôi.
- **US02 (Đăng nhập Hàng ngày)**: *Là một người dùng hợp lệ*, tôi muốn hệ thống yêu cầu đăng nhập (hoặc tự động duy trì phiên nếu chọn Ghi nhớ) mỗi khi khởi động lại ứng dụng, *để* bảo vệ không gian riêng tư.
- **US03 (Bảo vệ Private Keys - Zero Trust)**: *Là một chuyên gia bảo mật*, tôi muốn mật khẩu của mình được sử dụng làm "chìa khóa" (Master Key) mã hóa các API Keys nhạy cảm (OpenAI, Gemini), *để* ngay cả khi mã độc hoặc hacker đánh cắp được file SQLite `.db` của tôi, chúng cũng không thể xài chùa tiền từ tài khoản Cloud LLM của tôi.
- **US04 (Đăng xuất Khẩn cấp)**: *Là một nhân viên văn phòng*, tôi muốn có nút Đăng xuất nhanh chóng hoặc phím tắt trước khi rời khỏi bàn làm việc, *để* ngay lập tức khóa mọi quyền truy cập vào trợ lý AI của mình.

---

## 2. Luồng Nghiệp Vụ (Business Process Flows)

### 2.1. Luồng Khởi Tạo Workspace (Đăng ký lần đầu)
Vì kiến trúc của Desktop App mang tính cá nhân hóa 1:1, hệ thống chỉ cho phép tồn tại **duy nhất 01 Master User** tại một thời điểm.
1. **Kiểm tra trạng thái**: Lúc App boot lên, Lõi Python truy vấn kiểm tra số lượng record trong bảng `users` (SQLite).
2. **Quyết định luồng (Routing)**:
   - Nếu `count(users) == 0`: Hệ thống trả về trạng thái `NEEDS_INITIALIZATION`. Giao diện tự động điều hướng về Form **Register**.
   - Nếu `count(users) > 0`: Trả về trạng thái `READY_FOR_AUTH`. Giao diện điều hướng về Form **Login**.
3. **Thực thi tạo tài khoản (Sign-up)**:
   - Người dùng nhập Username, Password và Confirm Password.
   - Frontend kiểm lỗi qua Zod và gửi Payload `POST /auth/register` qua Backend.
   - Backend sử dụng thuật toán `bcrypt` (hoặc `argon2`) băm mật khẩu, lưu Hash vào DB.
   - Lấy chuỗi Password gốc của User đi qua hàm Key Derivation (vd: PBKDF2) để tạo Master Key. Key này sẽ được sử dụng cho SQLCipher.
   - Sinh JWT Token, lưu `sessions` và trả về Client.

### 2.2. Luồng Đăng Nhập (Login)
1. **Input**: User nhập thông tin Username & Password trên UI.
2. **Backend Verification**:
   - Trích xuất user theo Username.
   - Dùng `bcrypt.checkpw()` so khớp chuỗi Password thô với `password_hash` lưu trong DB.
   - Nếu sai: Trả về HTTP `401 Unauthorized`. (Cần cấu hình Rate Limit: Sai 5 lần khóa tạm 3 phút để chống Bruteforce cục bộ).
   - Nếu đúng:
     - Dùng Password thô tái tạo lại Master Key để giải mã API Keys (nạp khóa vào RAM).
     - Tạo một dòng mới trong bảng `sessions` lưu `token` (chuỗi JWT).
     - Thiết lập `expires_at` (vd: thời hạn 7 ngày).
3. **Frontend Sync**: Nhận chuỗi JWT Token, lưu trữ an toàn vào `localStorage` (hoặc State/Zustand), chuyển cảnh (GSAP Timeline 2) sang `MainLayout`.

### 2.3. Luồng Đăng Xuất & Thu Hồi (Logout/Revoke)
1. **Trigger**: Người dùng chủ động click nút "Đăng xuất" ở Sidebar hoặc System Tray.
2. **Frontend Action**: 
   - Xóa ngay lập tức JWT Token khỏi bộ nhớ Local.
   - Gửi request `POST /auth/logout` lên Lõi Python.
   - Force Redirect (đá văng) người dùng về giao diện `/login`.
3. **Backend Action**: 
   - Nhận yêu cầu, kiểm tra Header. Update bảng `sessions` của Token đó thành `is_revoked = 1`.
   - Tiêu hủy (Zeroing) Master Key đang được cache trong RAM tiến trình Python.
   - Đóng toàn bộ các kết nối WebSocket đang mở thuộc phiên đăng nhập đó.

---

## 3. Quy Tắc Phân Quyền (Router & Security Guards)

### 3.1. Rào chắn Frontend (React Router Guards)
- **Token Check Lifecycle**: Trước khi render bất kỳ màn hình nào, Router phải check tính hợp lệ tương đối (sự tồn tại) của Token.
- **Vùng Cấm (Unauthenticated Guard)**: Nếu không có Token, **MỌI TRUY CẬP** vào `/chat` (Main Chat) hoặc `/settings` (Cấu hình hệ thống) đều bị chặn đứng ở mức Component và ép Redirect về `/login`.
- **Vùng Đã Xác Thực (Authenticated Guard)**: Trái lại, nếu đã có Token hợp lệ, nếu User cố tình gõ url `/login` hoặc `/register`, Router sẽ tự động điều hướng ngược vào lại `/chat` để tránh luồng lặp.

### 3.2. Rào chắn Backend (FastAPI / WebSocket Guards)
- **HTTP Middleware (API)**: Mọi REST endpoint thực thi lệnh (ngoại trừ whitelist `/auth/register` và `/auth/login`) bắt buộc phải đính kèm header `Authorization: Bearer <JWT_TOKEN>`. Middleware Backend sẽ Decode JWT, kiểm tra bảng `sessions` (Phải khớp 2 điều kiện: `is_revoked == 0` và thời gian hiện tại `< expires_at`).
- **WebSocket Handshake**: Vì ứng dụng sử dụng WebSocket làm mạch máu giao tiếp thời gian thực, gói tin (Packet) đầu tiên Frontend gửi lên sau khi mở WS Connection phải là gói tin Xác Thực.
  - Ví dụ Payload: `{"type": "AUTHENTICATE", "token": "ey..."}`.
  - **Fail**: Nếu Token sai hoặc hết hạn, Lõi Python lập tức đóng chốt kết nối bằng mã `1008 Policy Violation`.
  - **Success**: Gắn `user_id` vào scope của tiến trình Connection hiện tại. Mọi gói tin (Event) bay qua luồng WS này về sau nghiễm nhiên được gán nhãn thuộc về User đó mà không cần gửi lại token.

---

## 4. Task Checklist Triển Khai Xác Thực

**Phía Backend (Python/Sidecar):**
- [ ] Cài đặt các package bảo mật cốt lõi: `bcrypt`, `pyjwt`, `passlib`.
- [ ] Xây dựng module `security.py` chịu trách nhiệm băm pass, verify password, và phát hành/giải mã chuẩn JWT.
- [ ] Khởi tạo 3 router cơ bản tại controller `/auth/register`, `/auth/login`, `/auth/logout`.
- [ ] Lập trình Dependency `get_current_user` cho FastAPI và tích hợp vào Middleware bảo vệ WebSocket Handshake.
- [ ] Xây dựng thuật toán sinh khóa (Key Derivation) từ mật khẩu để mã hóa kho API Keys cục bộ.

**Phía Frontend (React/Tauri):**
- [ ] Xây dựng Custom Hook `useAuth` để bao bọc các lời gọi API xác thực, lưu giữ State đăng nhập toàn cục.
- [ ] Viết HOC (Higher-Order Component) `<ProtectedRoute>` bọc quanh các Route `/chat` và `/settings` trong react-router.
- [ ] Thiết lập Axios Interceptor (hoặc Fetch wrap) tự động "đính kèm" Bearer Token vào mọi Request HTTP gửi tới cổng Sidecar.
- [ ] Cài đặt cơ chế "Auto-Logout" khi bắt được mã lỗi `HTTP 401 Unauthorized` từ Backend (Đề phòng trường hợp Token hết hạn lúc App đang chạy).
