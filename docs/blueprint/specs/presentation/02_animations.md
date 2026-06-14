# Đặc tả Hiệu ứng & Chuyển động (Animations & Transitions)

Tài liệu này quy định các tiêu chuẩn và kỹ thuật triển khai chuyển động (Animation) cho giao diện Autonomous AI Assistant (AAA). Ứng dụng sử dụng **GSAP (GreenSock)** kết hợp với Hook `@gsap/react` (`useGSAP`) nhằm đảm bảo hiệu năng cao nhất, mượt mà và không gây xung đột với chu trình render của React.

---

## 1. Ràng Buộc Hiệu Năng (Performance Rules)

Đây là các nguyên tắc **SỐNG CÒN** khi thiết kế hiệu ứng cho ứng dụng AAA:
- **Tách biệt Layout và Animation**: Hệ thống lưới (Flexbox/Grid), kích thước (width/height), và vị trí tuyệt đối (top/left) phải do CSS tĩnh (Tailwind) quyết định cấu trúc cứng.
- **GSAP Only Triggers Compositor**: GSAP CHỈ được phép can thiệp vào các thuộc tính Hardware Accelerated: `transform` (x, y, scale, rotation) và `opacity`. Tuyệt đối CẤM animate các thuộc tính như `width`, `height`, `margin`, `padding` để tránh kích hoạt luồng Layout Reflow/Paint gây sụt giảm FPS.
- **Snappy Micro-interactions**: Thời gian cho các tương tác nhỏ (click button, hover menu) dao động từ `0.15s` đến `0.3s`. Các hiệu ứng vòng lặp (looping) báo hiệu trạng thái hệ thống có thể chậm và mềm mại hơn.

---

## 2. Đặc Tả Các Timeline Cốt Lõi

### 2.1. Timeline 1: Trạng Thái AI Tư Duy (AI Thinking State)
Dùng để báo hiệu AI đang phân tích dữ liệu ngầm (Planning) hoặc chờ phản hồi từ LLM API, tránh để người dùng có cảm giác ứng dụng bị treo.
- **Kỹ thuật**: Infinite Loop Timeline.
- **Hiệu ứng**:
  - **Pulse Core**: Icon trung tâm phóng to thu nhỏ nhẹ (`scale: 0.95` -> `1.05`) kết hợp đổi độ sáng mượt mà.
  - **Border Glow**: Một vệt sáng (shadow gradient) chạy vòng quanh mép kính (Glassmorphism border) thông qua việc animate xoay (`rotation`) một pseudo-element chìm phía sau khung chứa với CSS `overflow: hidden`.

```javascript
// Pseudo-code mẫu cấu hình GSAP cho AI Thinking Indicator
useGSAP(() => {
  const tl = gsap.timeline({ repeat: -1, yoyo: true });
  
  // Hiệu ứng nhịp thở cho Icon trung tâm
  tl.to(".ai-core-icon", {
    scale: 1.05,
    opacity: 1,
    duration: 1.2,
    ease: "sine.inOut"
  }, 0);

  // Hiệu ứng xoay vệt sáng viền (Glow spinner)
  gsap.to(".ai-border-glow", {
    rotation: 360,
    duration: 3,
    repeat: -1,
    ease: "linear",
    transformOrigin: "center center"
  });
}, { scope: containerRef });
```

### 2.2. Timeline 2: Chuyển Cảnh Tổng Thể (Page & View Transitions)
Quản lý sự xuất hiện mượt mà giữa các khối màn hình lớn, dẫn dắt ánh nhìn của người dùng.
- **Chuyển từ Đăng nhập (Auth) -> Main Chat**:
  - Form Auth mờ dần và lùi chìm xuống: `opacity: 1 -> 0`, `y: 0 -> 20`, `duration: 0.4s`, `ease: "power2.in"`.
  - Main Chat UI hiện dần lên từ phía dưới: `opacity: 0 -> 1`, `y: 30 -> 0`, `duration: 0.6s`, `ease: "expo.out"`. Bắt đầu (delay) ngay sau khi khối Auth đã out hoàn toàn để tránh giật giao diện.
- **Thông báo đẩy (Proactive Toasts)**:
  - Khi Alert Engine phát tín hiệu, Toast Panel trượt lên từ góc dưới cùng bên phải màn hình: `y: 50 -> 0`, `opacity: 0 -> 1`, kèm theo hiệu ứng nảy nhẹ siêu mượt `ease: "back.out(1.5)"`.
  - Khi tắt/xóa: Trượt ngược xuống dưới `y: 0 -> 50`, `opacity: 0` nhanh chóng (`0.2s`).

### 2.3. Timeline 3: Hiệu Ứng Streaming (AI Text Reveal)
Khi LLM trả về từng cụm token (Streaming), việc render trực tiếp chuỗi văn bản dài ra liên tục dễ gây giật cục khung UI (Layout Shift).
- **Giải Pháp Chống Layout Shift**: Khung chứa tin nhắn (`MessageBubble`) phải được CSS cố định định dạng tràn (overflow) và hệ thống khung cha phải dùng auto-scroller tự do.
- **Kỹ Thuật Text Reveal**: 
  - Tránh hiệu ứng Typewriter từng ký tự do tốn tài nguyên React render liên tục. Dùng hiệu ứng **Fade In cụm từ**.
  - Khi một chunk văn bản mới (token) được stream về, đưa nó vào một thẻ `<span>` ẩn (`opacity: 0`, `y: 5`), sau đó dùng `gsap.to()` đẩy `opacity: 1` và `y: 0` siêu tốc (`duration: 0.1s`). Điều này tạo cảm giác văn bản đang "trồi lên" nhịp nhàng chứ không bị khựng cứng.

---

## 3. Hệ Thống Easing Tiêu Chuẩn

Nhằm tạo ra tính đồng nhất trong toàn bộ App, AAA tuân thủ quy chuẩn đường cong gia tốc (Easing Curves) sau:
- `power2.out` (Deceleration): Dùng cho các phần tử bay *vào* màn hình (Toasts, Popups, Modals) -> Chậm dần khi tới đích, tạo cảm giác an toàn và dễ kiểm soát.
- `power2.in` (Acceleration): Dùng cho các phần tử biến mất *ra khỏi* màn hình -> Nhanh dần khi rời đi, không gây vướng víu.
- `expo.out`: Dùng cho chuyển cảnh toàn màn hình (Page Transition) tạo sự hiện đại, ấn tượng cực mạnh ở đầu chuyển động.
- `back.out(1.2)`: Dùng khi cảnh báo hoặc xuất hiện tính năng mới, tạo độ nảy đàn hồi (bouncy) tự nhiên thu hút mắt.

---

## 4. Task Checklist Khởi Tạo Chuyển Động

Nhóm Frontend cần tạo cấu trúc sau trong mã nguồn React:

- [ ] Cài đặt gói `gsap` và hook chính chủ `@gsap/react`. Đăng ký `gsap.registerPlugin(useGSAP)`.
- [ ] Khởi tạo Component độc lập `AiThinkingIndicator.tsx` đóng gói riêng Timeline 1 (Pulse & Glow).
- [ ] Xây dựng Wrapper Component `PageTransition.tsx` bao bọc các Route để xử lý luồng Fade-up/Fade-down cho Timeline 2.
- [ ] Xây dựng hệ thống quản lý danh sách Toast bằng Component `ToastContainer.tsx`, xử lý mount/unmount kèm theo GSAP `back.out`.
- [ ] Tạo module `StreamingTextReveal.tsx` tối ưu hóa riêng cho Timeline 3: Kết hợp React state để tách chunk token và kích hoạt GSAP animate cho các thẻ `span` chữ cuối cùng được thêm vào đoạn chat.
