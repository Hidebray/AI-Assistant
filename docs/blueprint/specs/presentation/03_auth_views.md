# Đặc tả Giao diện Xác thực (Auth Views Specification)

Tài liệu này quy định cấu trúc component, kỹ thuật dàn trang và luồng tương tác cho phân hệ Xác thực (Authentication) của dự án AAA. Giao diện Auth đóng vai trò là điểm chạm đầu tiên, cần thể hiện rõ ngôn ngữ thiết kế Glassmorphism và mang lại cảm giác phản hồi mượt mà tuyệt đối.

---

## 1. Cấu Trúc Khung Màn Hình (View Structure & Layout)

Để đảm bảo hiệu năng, chống Layout Shift (nhảy DOM) khi GSAP hoạt động hoặc khi thông báo lỗi xuất hiện, toàn bộ cấu trúc được neo bằng hệ thống Flexbox với kích thước ràng buộc chặt chẽ.

### 1.1. `AuthLayout` (Container Khung)
- **Vai trò**: Component cha, quản lý ảnh nền Desktop mờ, vùng kéo thả (Drag Region) của Tauri và căn giữa nội dung.
- **Dàn trang**: Sử dụng `min-h-screen w-full flex items-center justify-center relative`. Thêm `overflow-hidden` để khóa scrollbar ngoài ý muốn.

### 1.2. Khung Form (Auth Card)
- **Vai trò**: Khối nền kính (Glassmorphism Level 2) chứa nội dung form Login hoặc Register.
- **Ràng buộc kích thước**: Khóa giới hạn chiều rộng bằng `w-full max-w-md` (tương đương 448px). Để tránh việc Card bị giật cục độ cao khi đổi từ Form ngắn sang Form dài, thiết lập `min-h-[500px]` hoặc sử dụng thủ thuật GSAP tự động animate `height` của Card cha.

---

## 2. Quản Lý Trạng Thái & Xác Thực (State & Validation)

Hệ thống sử dụng bộ đôi **React Hook Form (RHF)** và **Zod** nhằm hạn chế tối đa số lần re-render, đảm bảo luồng gõ phím của người dùng luôn đạt 60fps.

### 2.1. Zod Schema (Mã Mẫu)
```typescript
import { z } from "zod";

// Schema cho form đăng nhập
export const loginSchema = z.object({
  username: z.string().min(3, "Tên đăng nhập phải chứa ít nhất 3 ký tự."),
  password: z.string().min(6, "Mật khẩu quá ngắn."),
});

export type LoginFormValues = z.infer<typeof loginSchema>;

// Schema cho form đăng ký
export const registerSchema = loginSchema.extend({
  confirmPassword: z.string()
}).refine((data) => data.password === data.confirmPassword, {
  message: "Mật khẩu xác nhận không khớp.",
  path: ["confirmPassword"],
});

export type RegisterFormValues = z.infer<typeof registerSchema>;
```

### 2.2. Chống Layout Shift Khi Có Lỗi (Error Message Container)
Thành phần hiển thị thông báo chữ đỏ bên dưới mỗi `<input>` bắt buộc phải được bọc trong một `div` có chiều cao cố định (VD: `h-5` hoặc `min-h-[20px]`).
- **Quy tắc**: Khi Input hợp lệ, phần text báo lỗi bị ẩn (`opacity-0`), nhưng khối `div` chứa nó **vẫn chiếm dụng không gian**. Nhờ vậy, khi chữ xuất hiện (`opacity-100`), các input nằm phía dưới sẽ không bị đẩy tụt xuống gây ức chế thị giác.

---

## 3. UI/UX & Glassmorphism Tích Hợp

Kế thừa trực tiếp từ `01_design_system.md`, các chi tiết được styling như sau:

### 3.1. Auth Card (Level 2 Glass)
- **Tailwind Classes**: `bg-slate-900/40 backdrop-blur-2xl border border-white/20 shadow-glass-widget rounded-2xl p-8 flex flex-col relative overflow-hidden`.

### 3.2. Form Input Fields (Level 3 Glass)
- **Bình thường**: `w-full h-12 px-4 bg-white/5 border border-white/10 rounded-lg text-white placeholder-slate-400 outline-none transition-all duration-300`.
- **Trạng thái Focus (Active)**: `focus:bg-white/10 focus:border-primary-500 focus:ring-1 focus:ring-primary-500`.
- **Trạng thái Lỗi (Error)**: Thay viền thành màu cảnh báo `border-red-500 focus:ring-red-500` và gọi timeline GSAP lắc nhẹ component (Shake Animation) để lôi kéo sự chú ý.

### 3.3. Nút Bấm Xác Nhận (Primary Button)
- **Trạng thái Hover & Click**: `bg-primary-500 hover:bg-primary-glow text-white shadow-lg hover:shadow-ai-glow transition-all duration-300 active:scale-95`.

---

## 4. Luồng Tương Tác (Interaction Flow)

### 4.1. Giao Tiếp API & Lưu Trữ Token
- Khi RHF xác nhận data hợp lệ (Submit) -> Gửi sự kiện tới Hook `useAuth` -> Giao tiếp với lõi Python Backend qua WebSocket (hoặc Tauri IPC).
- Lõi AI trả về kết quả (thành công + JWT Token / Session ID).
- Lưu thông tin an toàn vào React Context và chuyển hướng sang Router chính (`MainLayout`).

### 4.2. Hiệu Ứng Chuyển Đổi Form với GSAP
Khi người dùng ấn "Chưa có tài khoản? Đăng ký ngay", form Login không tự nhiên biến mất mà sẽ được xử lý bằng Animation Timeline (đảm bảo không chặn event gõ phím):
1. **Unmount mượt**: Form Login mờ đi và trượt sang trái (`opacity: 0, x: -30`, `duration: 0.3s`, `ease: "power2.in"`).
2. **Mount mượt**: Form Register trượt vào từ bên phải (`opacity: 1, x: 0`, `duration: 0.4s`, `ease: "power2.out"`).
3. **Morphing Height**: Auth Card tự động điều chỉnh chiều cao (`gsap.to(cardRef, { height: 'auto', duration: 0.4 })`) để chứa vừa số lượng input dài hơn của form đăng ký.

---

## 5. Task Checklist Khởi Tạo UI Auth

- [ ] Cài đặt thư viện: `react-hook-form`, `@hookform/resolvers`, `zod`, và thư viện Icon (vd: `lucide-react` để làm icon hình con mắt ẩn/hiện mật khẩu).
- [ ] Thiết lập file `src/schemas/auth.schema.ts` định nghĩa logic kiểm lỗi.
- [ ] Khởi tạo Custom Hook `src/hooks/useAuth.ts` xử lý logic Call API, giữ state (Loading/Error) và lưu trữ JWT.
- [ ] Xây dựng Component cốt lõi `AuthInput.tsx`: Đóng gói `<input>`, nhãn `<label>`, thiết lập CSS chuẩn Glassmorphism và thẻ `div` giữ khung cố định để chống Layout Shift.
- [ ] Tạo `AuthLayout.tsx` thiết lập giao diện nền tối và vùng Drag Tauri.
- [ ] Lắp ráp `LoginForm.tsx` và `RegisterForm.tsx` tiêu thụ `AuthInput` và React Hook Form.
- [ ] Sử dụng `useGSAP` trong `AuthLayout.tsx` để điều phối hiệu ứng Slide Left/Right mượt mà giữa 2 form mà không làm lag luồng nhập liệu.
