# Đặc tả Giao diện Chạy ngầm & Khay Hệ thống (System Tray & Background UI)

Tài liệu này là mảnh ghép cuối cùng của tầng Giao diện (Presentation Layer), đặc tả cách thức tương tác Native Desktop của dự án AAA khi ứng dụng thu mình xuống chạy ngầm. Hệ thống tận dụng sức mạnh của Tauri API để cung cấp trải nghiệm liền mạch, phản hồi tức thời mà không chiếm dụng không gian làm việc của người dùng.

---

## 1. Tích Hợp Native & Hiệu Năng (Native Integration & Performance)

Ứng dụng AAA được thiết kế với triết lý cốt lõi: "Hoạt động ngầm - Báo cáo đúng lúc".
- **Tiết kiệm RAM**: Khi người dùng nhấn nút Đóng (X) ở cửa sổ chính, tiến trình React và WebView không bị tiêu diệt hoàn toàn mà chỉ chuyển sang trạng thái ẩn (`hide`). Các cảnh báo được đẩy lên hệ điều hành thông qua Native OS Notifications.
- **Tauri Global Shortcuts**: Đăng ký các phím tắt cấp hệ điều hành (Ví dụ: `Alt + Space` hoặc `Ctrl + Shift + Space`) để lập tức đánh thức Lõi AI từ bất cứ đâu.

---

## 2. Đặc Tả Khay Hệ Thống (System Tray Menu)

Một Icon nhỏ gọn sẽ luôn thường trực tại Taskbar (Windows) hoặc Menu Bar (macOS). Click chuột phải vào Icon sẽ mở ra **Context Menu** Native do Rust/Tauri quản lý hoàn toàn để đảm bảo tốc độ phản hồi 0ms.

### Các mục trong Context Menu:
1. **Show Main App (Mở giao diện chính)**: Đánh thức và làm nổi bật (`bringToFront`) cửa sổ Chat trung tâm.
2. **Pause Background Sync (Tạm dừng Đồng bộ ngầm)**: Tạm thời vô hiệu hóa Event Bus và khóa luồng mạng của các Plugin cào dữ liệu (Cron Jobs) để tiết kiệm pin/RAM khi chơi game. Icon khay hệ thống sẽ tự đổi sang màu xám.
3. **Settings (Cài đặt)**: Gọi trực tiếp cửa sổ Overlay Settings.
4. **Quit (Thoát hoàn toàn)**: Lệnh sát thủ. Gửi tín hiệu Graceful Shutdown tới cả luồng React và tiến trình Sidecar Python trước khi tự tiêu hủy an toàn.

**Mẫu cấu hình Tauri (Rust Snippet):**
```rust
use tauri::{SystemTray, SystemTrayMenu, CustomMenuItem, SystemTrayEvent};

pub fn create_tray() -> SystemTray {
    let show = CustomMenuItem::new("show".to_string(), "Mở trợ lý AAA");
    let pause = CustomMenuItem::new("pause".to_string(), "Tạm dừng Đồng bộ");
    let settings = CustomMenuItem::new("settings".to_string(), "Cài đặt...");
    let quit = CustomMenuItem::new("quit".to_string(), "Thoát hoàn toàn");
    
    let tray_menu = SystemTrayMenu::new()
        .add_item(show)
        .add_item(pause)
        .add_native_item(tauri::SystemTrayMenuItem::Separator)
        .add_item(settings)
        .add_native_item(tauri::SystemTrayMenuItem::Separator)
        .add_item(quit);
        
    SystemTray::new().with_menu(tray_menu)
}
```

---

## 3. Giao Diện Hội Thoại Nhanh (Spotlight Overlay)

Để tránh thao tác thừa thãi (mở Full App) khi người dùng chỉ muốn giao một lệnh đơn giản (Ví dụ: "Nhắc tôi uống thuốc lúc 3h chiều" hay "Tắt nhạc"), hệ thống cung cấp giao diện Mini-chat tốc độ cao.

### 3.1. Đặc tả UI/UX
- **Kích hoạt**: Bấm `Alt + Space`. Cửa sổ trong suốt đè lên chính giữa màn hình hiện tại.
- **Thiết kế Cực Giản (Minimalist)**: Tương tự Spotlight của macOS hoặc PowerToys Run của Windows.
  - Cấu thành từ một ô Input khổng lồ duy nhất (Level 2 Glassmorphism: `bg-slate-900/60 backdrop-blur-3xl shadow-2xl`), viền bo góc tròn mềm mại (`rounded-full` hoặc `rounded-2xl`).
  - Font chữ lớn (Text 2xl) tập trung ánh nhìn.
- **Trải nghiệm**: Input phải kích hoạt Auto-focus ngay lập tức khi xuất hiện. Gõ lệnh -> Nhấn `Enter` -> Submit thẳng vào Event Bus -> Cửa sổ tự động tàng hình ngay lập tức (nhường tiến trình xử lý nền cho Backend). Nhấn `Escape` để hủy và đóng.

---

## 4. Hệ Thống Thông Báo Đẩy Chủ Động (Native OS Notifications)

Khi Lõi AI (AgentCore / AlertEngine) phân tích và phân loại các thông tin thu thập ngầm là "Khẩn cấp" hoặc sự kiện tự động (như Lịch/Task), hệ thống sẽ sử dụng thư viện `@tauri-apps/plugin-notification` để bắn thông báo nguyên bản (Native) của hệ điều hành.

### 4.1. Lợi Ích Của Native Notification
- **Vượt ra ngoài cửa sổ**: Người dùng vẫn nhận được cảnh báo ngay cả khi họ thu nhỏ ứng dụng, đang chơi game ở chế độ toàn màn hình hoặc làm việc trên các cửa sổ khác.
- **Độ tin cậy cao**: Tận dụng Action Center của Windows hoặc Notification Center của macOS để lưu trữ lịch sử thông báo nếu người dùng lỡ tay tắt.

### 4.2. Cơ Chế Fallback
Trong trường hợp OS từ chối quyền gửi Notification (User Denied Permission), hệ thống sẽ **Gracefully Degrade** (Chuyển đổi dự phòng) về dạng In-app Toast Component (`ToastContainer.tsx`) để đảm bảo thông tin luôn được truyền tải.

---

## 5. Task Checklist Tích Hợp Native & Khay Hệ Thống

- [x] Cấu hình file `tauri.conf.json` để cấp quyền (Allowlist) sử dụng System Tray API và Global Shortcuts API.
- [x] Viết mã Rust trong thư mục `src-tauri/src/main.rs` để khởi tạo menu chuột phải (Context Menu) cho System Tray và xử lý các sự kiện click menu tương ứng.
- [ ] Đăng ký hook bắt tổ hợp phím (Global Shortcut) phía Frontend qua thư viện `@tauri-apps/api/globalShortcut` để trigger giao diện Spotlight Overlay.
- [ ] Xây dựng Component tĩnh `SpotlightSearch.tsx` có CSS chuẩn Glassmorphism, thiết lập cờ tự động focus (auto-focus), kết nối luồng gửi Event mệnh lệnh xuống Backend.
- [x] Cài đặt plugin `@tauri-apps/plugin-notification` và yêu cầu quyền (Request Permission) lúc ứng dụng khởi động (`MainLayout.tsx`).
- [x] Thiết lập cơ chế Fallback xuống In-app Toast nếu người dùng từ chối cấp quyền OS Notification.
- [x] Viết script `Graceful Shutdown` trong tầng Rust đảm bảo khi user bấm "Thoát hoàn toàn" (Quit), cả Tauri WebView và luồng ngầm Python Sidecar đều được kill sạch.
