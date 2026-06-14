# Hệ thống Thiết kế & Giao diện (Design System Specification)

Tài liệu này đóng vai trò là "chân lý thiết kế" (Source of Truth) cho toàn bộ tầng Giao diện (Presentation Layer) của dự án Autonomous AI Assistant (AAA). Ứng dụng Desktop sử dụng **React + Tauri**, tuân thủ nghiêm ngặt ngôn ngữ thiết kế **Glassmorphism** tối giản, mang lại trải nghiệm thị giác cao cấp (premium) và tương lai.

---

## 1. Ràng Buộc Phong Cách & Môi Trường (Style & Environment)
- **Môi trường**: Ứng dụng Desktop chạy nền (System Tray / Frameless Window).
- **Chủ đề**: Native Dark Mode là chế độ mặc định và ưu tiên cao nhất để làm nổi bật sự mờ ảo của hiệu ứng kính.
- **Triết lý**: Less is More. Hạn chế sử dụng khối đặc (solid blocks), ưu tiên sử dụng độ trong suốt (opacity), viền mờ (subtle borders) và đổ bóng đa tầng (soft shadows).

---

## 2. Bảng Màu & Typography (Color Palette & Typography)

### 2.1. Cấu hình Typography (Phông chữ)
Hệ thống sử dụng bộ phông chữ hiện đại, tối ưu cho cả giao diện đọc và hiển thị code.
- **Font Chủ Đạo (Sans-serif)**: `Inter` (Sạch sẽ, rõ nét trên màn hình độ phân giải cao).
- **Font Code (Monospace)**: `Roboto Mono` hoặc `Fira Code` (Để hiển thị các output code block từ LLM).

### 2.2. Bảng Màu Thiết Kế (Color Tokens)
Các màu sắc được định nghĩa thông qua biến CSS (CSS Variables) để dễ dàng hỗ trợ Theme Switching, nhưng Dark Mode sẽ là base.

- **Nền Giao Diện (Background)**: `bg-transparent` để lộ hình nền Desktop của người dùng, hoặc `bg-[#0B0F19]/60` nếu cần độ tối sâu hơn.
- **Màu Nhấn (Primary / AI Glow)**: Dùng để biểu thị AI đang suy nghĩ hoặc các nút CTA chính.
  - Primary Base: `#6366F1` (Indigo-500)
  - Primary Glow: `#8B5CF6` (Violet-500) kết hợp Drop Shadow phát sáng.
- **Màu Văn Bản (Text)**:
  - Heading & Primary Text: `#F8FAFC` (Slate-50)
  - Muted/Secondary Text: `#94A3B8` (Slate-400)

---

## 3. Các Cấp Độ Glassmorphism (Glass Levels Utilities)

Hệ thống phân chia hiệu ứng kính mờ thành 3 cấp độ (Levels) để tạo chiều sâu không gian (Depth of Field) cho các Component UI.

### Level 1: Nền Cửa Sổ Chính (Base Glass Background)
Dành cho `MainLayout` hoặc cửa sổ Chat chính. Độ mờ vừa phải để lộ hình nền Desktop.
- **Tailwind Classes**: `bg-black/20 backdrop-blur-xl border border-white/10 shadow-2xl rounded-2xl`

### Level 2: Bảng Điều Khiển Nổi (Floating Widgets / Toasts / Sidebar)
Dành cho các popup thông báo hoặc menu cài đặt đè lên trên lớp nền chính.
- **Tailwind Classes**: `bg-slate-900/40 backdrop-blur-2xl border border-white/20 shadow-[0_8px_30px_rgb(0,0,0,0.12)] rounded-xl`

### Level 3: Các Nút Bấm & Input (Interactive Elements)
Dành cho ô nhập liệu chat, nút gửi, các toggle switch. Cần độ nổi và tương phản cao hơn khi hover.
- **Trạng thái bình thường**: `bg-white/5 border border-white/10 rounded-lg text-white shadow-sm transition-all duration-300`
- **Trạng thái Hover (Hover State)**: `hover:bg-white/10 hover:border-white/30 hover:shadow-[0_0_15px_rgba(99,102,241,0.4)]`

---

## 4. Hệ Thống Grid & Layout Tổng Thể (Global Layout System)

### 4.1. Kiến Trúc Cửa Sổ Không Viền (Frameless Window)
Ứng dụng Tauri sẽ được cấu hình bỏ thanh tiêu đề mặc định của OS (`decorations: false` trong `tauri.conf.json`).

### 4.2. Khung Kéo Cửa Sổ (Drag Region)
Do bỏ thanh tiêu đề mặc định, cần thiết lập một vùng Header siêu mỏng ở trên cùng giao diện để người dùng di chuyển cửa sổ.
- **Tauri Attribute**: Gắn thẻ `data-tauri-drag-region` vào thẻ `<header>`.
```tsx
// Ví dụ Header Component
<header 
  data-tauri-drag-region 
  className="h-10 w-full flex items-center justify-between px-4 select-none cursor-move"
>
   {/* Window Controls (Close, Minimize) */}
</header>
```

---

## 5. Mẫu Cấu Hình Tailwind (Tailwind Config Sample)

Để kích hoạt hệ thống thiết kế trên, file `tailwind.config.js` của dự án sẽ được thiết lập mở rộng như sau:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // Bắt buộc Dark Mode
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['Roboto Mono', 'monospace'],
      },
      colors: {
        primary: {
          500: '#6366F1',
          glow: '#8B5CF6',
        },
        glass: {
          base: 'rgba(0, 0, 0, 0.2)',
          widget: 'rgba(15, 23, 42, 0.4)',
          element: 'rgba(255, 255, 255, 0.05)',
        }
      },
      boxShadow: {
        'glass-widget': '0 8px 30px rgba(0,0,0,0.12)',
        'ai-glow': '0 0 20px rgba(139, 92, 246, 0.5)',
      },
      backdropBlur: {
        'xs': '2px',
      }
    },
  },
  plugins: [],
}
```

---

## 6. Task Checklist Khởi Tạo Frontend

- [ ] Khởi tạo dự án Tauri kết hợp React/TypeScript (chạy lệnh `npx create-tauri-app`).
- [ ] Cài đặt Tailwind CSS, PostCSS và Autoprefixer cho môi trường Vite/React.
- [ ] Import font `Inter` và `Roboto Mono` vào `index.html` hoặc qua file CSS tổng.
- [ ] Dán file mẫu `tailwind.config.js` đã thiết kế ở trên vào dự án.
- [ ] Thiết lập `index.css` với các base layer (reset styles).
- [ ] Cấu hình file `tauri.conf.json`: Đặt `"decorations": false` và `"transparent": true` để mở khóa khả năng hiển thị nền Desktop phía sau cửa sổ ứng dụng.
- [ ] Xây dựng một file `GlassComponents.tsx` nháp để render thử cả 3 Level kính nhằm đảm bảo màu sắc và độ mờ hiển thị đúng với thiết kế.
