# Đặc tả Cấu trúc Triển khai Production (Production Deployment Specs)

## 1. Bài toán Đóng gói (Packaging Challenge)

Ứng dụng Autonomous AI Assistant (AAA) có một mô hình kết hợp (Hybrid Model) khá độc đáo:
- **Frontend**: Tauri (Viết bằng Rust, hiển thị UI qua Webview React/Vite).
- **Backend**: FastAPI (Viết bằng Python, chạy dưới dạng một ASGI Server qua Uvicorn).

Trong giai đoạn Development, chúng ta khởi chạy hai tiến trình này độc lập (qua `npm run tauri dev` và `uvicorn main:app`). Tuy nhiên, khi phân phối ứng dụng cho người dùng cuối (End-users) trên môi trường Production, không thể yêu cầu người dùng phải tự cài đặt Python, cấu hình môi trường ảo (`venv`), cài `pip install`, và gõ lệnh dòng lệnh được.

## 2. Giải pháp: Kiến trúc Tauri Sidecar + PyInstaller

Để mang lại trải nghiệm Native Desktop hoàn hảo (Chỉ cần 1 cú click đúp để mở phần mềm), chúng ta áp dụng mô hình **Tauri Sidecar**.

### 2.1. Tauri Sidecar là gì?
Sidecar là tính năng mạnh mẽ của Tauri cho phép nhúng (bundle) một hoặc nhiều file thực thi độc lập (executable binaries) vào chung với bộ cài đặt gốc của ứng dụng Tauri. 
Khi ứng dụng Tauri khởi chạy, nó có thể tự động gọi (spawn) các file Sidecar này chạy ngầm dưới nền, và khi Tauri tắt, nó cũng tự động dọn dẹp (kill) tiến trình Sidecar.

### 2.2. Quy trình Hoạt động

1. **Giai đoạn Đóng gói (Build Time)**:
   - Dùng `PyInstaller` biên dịch toàn bộ thư mục `backend/` thành một file thực thi duy nhất (VD: `backend-win-x86_64.exe` trên Windows). Toàn bộ Python interpreter và các thư viện dependencies sẽ được "nén" vào trong file này.
   - Chép file `.exe` này vào thư mục cấu hình của Tauri (`frontend/src-tauri/bin/`).
   - Cấu hình file `tauri.conf.json` để khai báo `backend` như một Sidecar.

2. **Giai đoạn Chạy (Runtime)**:
   - Người dùng click mở `AAA.exe`.
   - Lõi Rust của Tauri kiểm tra hệ điều hành (Windows/Mac/Linux) và tự động tìm file Sidecar tương ứng (VD: `backend-win-x86_64.exe`).
   - Tauri khởi chạy Sidecar ở một cổng ngầm (VD: `8000`).
   - Giao diện UI (React) load lên, gọi API đến `localhost:8000`. Người dùng hoàn toàn không biết có một server Python đang chạy ngầm phía dưới!

## 3. Lợi ích của Kiến trúc này

1. **Plug & Play (Zero Setup)**: Người dùng tải về là dùng ngay, không cần cài đặt Python.
2. **Bảo vệ Mã nguồn (Source Protection)**: Code Python được PyInstaller biên dịch và đóng gói, hạn chế việc bị xem lén hoặc sửa đổi trái phép so với việc để raw `.py`.
3. **Quản lý Tài nguyên chặt chẽ**: Tauri quản lý vòng đời của Backend. Khi user tắt App, Backend cũng bị tắt theo một cách an toàn, không để lại các tiến trình "zombie" ngốn RAM.
4. **Vẫn duy trì tính Local-First tuyệt đối**: Dữ liệu và AI xử lý 100% trên máy người dùng, không phụ thuộc Server bên thứ 3.

## 4. Hướng dẫn Build (Script `build_sidecar.ps1`)

Đội ngũ phát triển đã chuẩn bị sẵn một script tự động `build_sidecar.ps1`. Chỉ cần một dòng lệnh, script này sẽ thực hiện toàn bộ quy trình:

1. Di chuyển vào thư mục `backend/`.
2. Dùng PyInstaller đóng gói `main.py` cùng với toàn bộ các thư viện và folder tĩnh (plugin, database, alembic...).
3. Tự động đổi tên file sinh ra thành định dạng chuẩn của Tauri (VD: `backend-x86_64-pc-windows-msvc.exe`).
4. Di chuyển file đó vào `frontend/src-tauri/bin/`.
5. Đội ngũ Frontend chỉ cần gõ lệnh `npm run tauri build` là xong!

---
*Ghi chú: Mô hình này hiện tại là tối ưu nhất cho AAA. Trong tương lai nếu dự án cần cung cấp AAA dưới dạng một Cloud SaaS, chỉ cần bóc tách file thực thi Backend đẩy lên Docker, còn UI Web sẽ trỏ API đến Server đó (Mô hình Client-Server truyền thống) mà không phải thay đổi bất kỳ dòng code logic nào nhờ Clean Architecture!*
