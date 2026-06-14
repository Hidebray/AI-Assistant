# Đặc tả Giao diện Cài đặt (Settings UI Specification)

Tài liệu này quy định cấu trúc tổ chức, bảo mật hiển thị và cách thức giao tiếp dữ liệu cho phân hệ Cài đặt và Quản lý Tiện ích (Settings & Plugin Management) của dự án AAA.

---

## 1. Cấu Trúc Khung Màn Hình (View Structure)

Để mang lại trải nghiệm làm việc tập trung (focused workspace) mà không bắt buộc người dùng rời khỏi cuộc hội thoại hiện tại, giao diện Cài đặt được thiết kế dưới dạng **Overlay Modal (Kính mờ phủ toàn màn hình)**.

### 1.1. `SettingsModal` Container
- Nền đen bán trong suốt `bg-black/60 backdrop-blur-sm`, đặt ở z-index cao nhất.
- Khối cài đặt chính ở trung tâm: Khung kính mờ Level 2 (`bg-slate-900/50 backdrop-blur-3xl`), kích thước rộng rãi (VD: `w-11/12 max-w-5xl h-[80vh]`), đổ bóng lớn tạo chiều sâu.

### 1.2. Sidebar Điều Hướng Nội Bộ (Internal Navigation)
Khối Settings được chia làm 2 cột:
- **Cột trái (Menu Điều Hướng)**:
  - **Chung (General)**: Quản lý Chủ đề (Theme), Phím tắt gọi nhanh toàn hệ thống (Global Shortcuts), Tự động khởi động cùng OS.
  - **Mô Hình AI (LLM Providers)**: Quản lý cài đặt Cloud LLM (OpenAI/Gemini API Key) và Local LLM (Ollama Base URL).
  - **Tiện ích mở rộng (Plugins)**: Trung tâm quản lý, cấp quyền và bật/tắt các module mở rộng Microkernel.
- **Cột phải (Content Area)**: Hiển thị nội dung form cấu hình chi tiết tương ứng với tab được chọn. Cột này hỗ trợ cuộn dọc độc lập (`overflow-y-auto`).

---

## 2. Bảo Mật Giao Diện (Security & Data Masking)

Giao diện cấu hình, đặc biệt là Tab `LLM Providers` chứa các dữ liệu vô cùng nhạy cảm. Việc rò rỉ API Key qua việc tình cờ share màn hình (Screen Sharing) là rủi ro rất cao.

- Các trường `API Key` hoặc `Access Token` bắt buộc mặc định sử dụng thẻ `<input type="password" />`.
- Tích hợp một nút bấm (Toggle Eye Icon) đính kèm trong ô input để người dùng chủ động xem chuỗi ký tự thô khi cần (đổi type sang `text`).
- Tương tự màn hình Auth, hệ thống cảnh báo kiểm lỗi (Zod Validation) khi người dùng nhập sai định dạng URL hay thiếu ký tự phải được neo layout cố định để không đẩy khối input xê dịch (Zero Layout Shift).

---

## 3. Giao Diện Quản Lý Tiện Ích (Plugin Management UI)

Khu vực này đọc danh sách Plugin từ Backend (thông qua luồng Event Bus lúc khởi động ứng dụng) và hiển thị trực quan cho người dùng.

### 3.1. Dàn Trang Tĩnh (Static Layout Constraint)
Sự đồng nhất thị giác trong màn hình quản lý tính năng là rất cần thiết. Danh sách thẻ hiển thị Plugin (Cards) bắt buộc được dàn bằng hệ thống **CSS Grid**.
- **Container**: Áp dụng `grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6`.
- **Ràng buộc**: Bất kể tên Plugin dài hay ngắn, nội dung chú thích (description) nhiều chữ hay ít chữ, Grid sẽ ép độ rộng các cột bằng nhau. 
- Văn bản áp dụng kĩ thuật cắt gọn dòng `line-clamp-2` (hiển thị tối đa 2 dòng, phần thừa ra dấu `...`), đảm bảo chiều cao thẻ Card luôn giữ tĩnh tuyệt đối (Ví dụ: `h-40`). Cấu trúc tĩnh này ngăn chặn hiệu ứng giật DOM khi người dùng kích hoạt Toggle Switch bên trong.

### 3.2. Mã Mẫu Đặc Tả Component `PluginCard`

```tsx
import React, { useState } from 'react';
import { Settings } from 'lucide-react'; // Thư viện Icon

interface PluginProps {
  id: string;
  name: string;
  version: string;
  source: string;
  description: string;
  isActive: boolean;
  hasConfig: boolean;
  onToggle: (id: string, newState: boolean) => void;
  onOpenConfig: (id: string) => void;
}

export const PluginCard: React.FC<PluginProps> = (props) => {
  const [loading, setLoading] = useState(false);

  const handleToggle = () => {
    setLoading(true);
    // Gửi sự kiện kích hoạt trạng thái Plugin
    props.onToggle(props.id, !props.isActive);
  };

  return (
    {/* Ràng buộc chiều cao tĩnh h-40 */}
    <div className="flex flex-col justify-between p-5 h-40 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-colors shadow-sm">
      
      {/* Header Card: Tên & Trạng thái */}
      <div className="flex justify-between items-start">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary-500/20 flex items-center justify-center text-primary-400">
            📦
          </div>
          <div>
            {/* Tên Plugin tĩnh, cắt chữ nếu quá dài */}
            <h3 className="font-semibold text-slate-100 truncate w-32" title={props.name}>{props.name}</h3>
            <p className="text-xs text-slate-400">{props.version} • {props.source}</p>
          </div>
        </div>
        
        {/* Toggle Switch */}
        <button 
          onClick={handleToggle}
          disabled={loading}
          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${props.isActive ? 'bg-green-500' : 'bg-slate-600'}`}
        >
          <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${props.isActive ? 'translate-x-6' : 'translate-x-1'}`} />
        </button>
      </div>

      {/* Description: Tối đa 2 dòng */}
      <p className="text-sm text-slate-300 mt-3 line-clamp-2 leading-relaxed">
        {props.description}
      </p>

      {/* Footer / Cài đặt Nâng cao */}
      {props.hasConfig && (
        <div className="mt-3 flex justify-end">
          <button 
            onClick={() => props.onOpenConfig(props.id)}
            className="flex items-center gap-1 text-xs text-primary-400 hover:text-primary-300 transition-colors"
          >
            <Settings size={14} /> Cấu hình
          </button>
        </div>
      )}
    </div>
  );
};
```

### 3.3. Modal Cấu Hình Chi Tiết Plugin (Plugin Setup Sub-Modal)
Nếu Plugin báo cáo có cờ `hasConfig = true` (ví dụ: Email Plugin cần cửa sổ đăng nhập OAuth2), khi click nút "Cấu hình", mở đè thêm một Modal con (Sub-Modal). Giao diện này sẽ render tự động các Form input dựa trên JSON Schema mà lõi Python gửi lên cho từng Plugin.

---

## 4. Tương Tác & Lưu Trữ Cấu Hình (Interaction & Storage)

### 4.1. WebSocket Payload & Hot-Reload
Khi người dùng thay đổi giá trị (Bật/tắt Plugin, Nhập API Key), tiến trình lưu dữ liệu diễn ra hoàn toàn tự động:
1. **Debounce Optimization**: Các Input text đợi độ trễ khoảng 500ms sau khi ngừng gõ để gom nhóm thay đổi.
2. **Gửi Payload lên Event Bus**: Lớp Giao tiếp UI gửi gói tin định dạng Pydantic Event:
   `{ "event_type": "User.SettingsChanged", "setting_key": "llm.openai_key", "new_value": "sk-xxx..." }`.
3. **Backend Phản Hồi**: Lõi Python nhận Event, ghi xuống Database SQLite. Cực kỳ quan trọng: Lõi thực hiện cơ chế **Hot-Reload** (Ví dụ: khởi tạo lại Object `HybridLLMAdapter` mới hoặc nạp module Plugin mới) trực tiếp vào RAM mà không yêu cầu khởi động lại ứng dụng.

### 4.2. Hiệu Ứng Phản Hồi Hình Ảnh (Visual Feedback)
- Việc lưu dữ liệu thành công KHÔNG CẦN và KHÔNG ĐƯỢC hiển thị Dialog hộp thoại Alert (OK/Cancel) làm phiền người dùng.
- Sử dụng hiệu ứng **Toast Notification siêu gọn**: Trượt một thẻ nhỏ dạng viên thuốc (Pill shape) từ trên đỉnh màn hình xuống (`y: -50 -> 0`) với thông điệp: `✓ Đã lưu cấu hình`.
- Hoặc hiển thị một gợn sóng ánh sáng xanh lá lướt nhẹ trên viền Card của Plugin vừa tương tác thành công.

---

## 5. Task Checklist Khởi Tạo Màn Hình Cài Đặt

- [ ] Xây dựng Component `SettingsModal.tsx` đóng vai trò là vỏ bọc Overlay bao phủ toàn hệ thống, với chỉ số z-index cao nhất.
- [ ] Cài đặt thanh điều hướng bên trái `SettingsSidebar.tsx` và cơ chế Router động/State nội bộ để chuyển Tab nội dung bên phải.
- [ ] Viết Component `LLMProviderSettings.tsx` tích hợp RHF chứa các Input nhạy cảm (có nút ẩn/hiện API Key dạng password) giữ khung CSS tĩnh.
- [ ] Lắp ráp kiến trúc `PluginManagerUI.tsx` và Component con `PluginCard.tsx`. Kiểm thử đảm bảo cấu trúc lưới CSS Grid (vd: `grid-cols-2` hoặc `3`) hiển thị đẹp và cố định trên các màn hình khác nhau.
- [ ] Viết Custom Hook `useSettingsSync.ts` chịu trách nhiệm Debounce các Input thay đổi, gửi sự kiện `SettingsChanged` qua WebSocket và lắng nghe phản hồi thành công từ Backend để kích hoạt Toast Notification nhẹ nhàng.
