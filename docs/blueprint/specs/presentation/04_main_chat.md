# Đặc tả Giao diện Trò chuyện Chính (Main Chat Specification)

Tài liệu này quy định cấu trúc kiến trúc, tiêu chuẩn render hiển thị, và luồng tương tác thời gian thực (Real-time) cho trái tim của ứng dụng AAA: Màn hình Trò chuyện Chính (Main Chat).

---

## 1. Cấu Trúc Màn Hình Tổng Thể (Overall View Structure)

Hệ thống sử dụng Flexbox cấp cao để chia không gian màn hình thành hai khu vực độc lập, đảm bảo Sidebar có thể ẩn/hiện mà không làm vỡ cấu trúc của Box Chat.

### 1.1. `MainLayout`
- Khung bọc ngoài cùng: Sử dụng `flex flex-row h-screen w-full bg-transparent overflow-hidden`.

### 1.2. `Sidebar` (Khu vực quản lý)
- **Thuộc tính Layout**: Cố định chiều rộng (VD: `w-72` hoặc `w-80`), `flex-shrink-0`, có thể thu gọn trượt sang trái (`-translate-x-full`) qua GSAP.
- **Nội dung**: Danh sách lịch sử hội thoại (Conversations), Trạng thái các Plugin đang chạy ngầm, Menu Cài đặt (Settings).

### 1.3. `ChatAreaContainer` (Khu vực tương tác chính)
- **Thuộc tính Layout**: Chiếm toàn bộ không gian còn lại (`flex-1 flex flex-col relative`).
- **Header**: Nằm sát trên cùng (`h-14 flex items-center justify-between px-6 border-b border-white/10`). Chứa:
  - Tên cuộc hội thoại hiện tại.
  - Tên LLM đang sử dụng (vd: `Local: Llama-3-8B` hoặc `Cloud: GPT-4o`).
  - **`AgentStatusIndicator`**: Khối trạng thái nhấp nháy phát sáng (Pulse Glow) đã định nghĩa ở phần Animations khi AI đang "suy nghĩ".

---

## 2. Đặc Tả Bong Bóng Tin Nhắn (Message Bubbles)

### 2.1. Ràng Buộc Layout Chống "Layout Shift"
**Nghiêm cấm** việc để `div` chứa văn bản tự do co giãn toàn màn hình (`width: auto`) trong khi text đang stream từng chữ một, điều này sẽ gây rung lắc liên tục toàn bộ UI, đặc biệt khi CSS Flexbox cố gắng căn chỉnh lại lề.
- Mọi bong bóng chat bắt buộc phải gắn thẻ `max-width` tuyệt đối (Ví dụ: `max-w-[85%] lg:max-w-3xl`).
- Đối với thẻ bọc khối Code Block hoặc Table sinh ra từ Markdown, bắt buộc cấu hình `w-full overflow-x-auto block` để chúng tự cuộn ngang, tránh trường hợp Code quá dài đẩy vỡ Flexbox của cha nó.

### 2.2. Phân Biệt Giao Diện (UI Differentiation)
- **User Message (`sender_role === 'user'`)**:
  - Nằm bám lề phải (`self-end`).
  - Style: `bg-primary-500/80 backdrop-blur-md rounded-2xl rounded-tr-sm text-white px-5 py-3 shadow-ai-glow`.
- **Agent Message (`sender_role === 'assistant'`)**:
  - Nằm bám lề trái (`self-start`).
  - Style: Kính mờ tĩnh lặng `bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl rounded-tl-sm text-slate-100 px-5 py-3 shadow-glass-widget`.

### 2.3. Tích Hợp Markdown & Syntax Highlighting
Sử dụng thư viện `react-markdown` kết hợp với `highlight.js` (hoặc `prismjs`) và `dompurify` để phòng chống nguy cơ chèn mã độc (XSS) triệt để.

**Mã mẫu Cấu trúc Component `MessageBubble.tsx`**:
```tsx
import React, { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import DOMPurify from 'dompurify';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface MessageProps {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export const MessageBubble: React.FC<MessageProps> = ({ role, content }) => {
  const isUser = role === 'user';
  
  // XSS Protection & Memoization (chống tiêm mã độc qua chat)
  const safeContent = useMemo(() => DOMPurify.sanitize(content), [content]);

  return (
    <div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'} mb-6`}>
      <div 
        // BẮT BUỘC RÀNG BUỘC KÍCH THƯỚC: max-w-3xl để chống vỡ Layout khi đang stream text
        className={`relative max-w-3xl w-fit break-words ${
          isUser 
            ? 'bg-primary-500/80 backdrop-blur-md rounded-2xl rounded-tr-sm px-5 py-3 text-white'
            : 'bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl rounded-tl-sm px-5 py-3 text-slate-100 shadow-glass-widget'
        }`}
      >
        <ReactMarkdown
          components={{
            code({ node, inline, className, children, ...props }) {
              const match = /language-(\w+)/.exec(className || '');
              return !inline && match ? (
                <div className="w-full overflow-x-auto rounded-md my-2"> {/* Chống vỡ bảng mã */}
                  <SyntaxHighlighter style={vscDarkPlus} language={match[1]} PreTag="div" {...props}>
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                </div>
              ) : (
                <code className="bg-black/30 rounded px-1.5 py-0.5 font-mono text-sm" {...props}>
                  {children}
                </code>
              );
            }
          }}
        >
          {safeContent}
        </ReactMarkdown>
      </div>
    </div>
  );
};
```

---

## 3. Khu Vực Nhập Liệu (Chat Input & Actions)

Nằm ở dưới cùng của màn hình, được bao bọc bởi một lớp kính mờ Level 2.

### 3.1. Textarea Auto-Resize
- **Logic**: Sử dụng tham chiếu `ref` để tự động tính toán và cập nhật `height` thẻ Textarea theo `scrollHeight` mỗi khi người dùng nhập văn bản mới.
- **Ràng buộc**: Đặt chiều cao tối đa (ví dụ: `max-h-40`), nếu văn bản vượt quá chiều cao này sẽ xuất hiện thanh cuộn trong (`overflow-y-auto`) để tránh ô nhập liệu khổng lồ che khuất toàn bộ màn hình đọc chat.

### 3.2. Cụm Nút Hành Động (Action Buttons)
- Đặt chung trong container input với layout dạng flex-row.
- `[+] Upload / Đính kèm`: Nút hình ghim kẹp để tải tệp tin lên RAG.
- `[x] Stop Generating`: Chỉ xuất hiện thay thế nút Gửi khi trạng thái hệ thống là `isStreaming === true`. Nhấn vào sẽ bắn WebSocket Event ngắt luồng xử lý của LLM và Dừng render chữ.
- `[ ] Clear Context (New Chat)`: Bắt đầu cuộc hội thoại mới tinh, dọn sạch bộ nhớ ngắn hạn.

---

## 4. Luồng Dữ Liệu Thời Gian Thực (WebSocket Integration)

Vấn đề lớn nhất của các ứng dụng React khi thực hiện luồng Stream Text từ LLM là Hiệu Năng (Performance). Nếu toàn bộ mảng `messages` lớn nằm ở Global State bị bắt cập nhật liên tục 20-30 lần/giây, cả màn hình chat sẽ Re-render toàn bộ dẫn đến lag giật và tụt FPS nghiêm trọng.

### Giải pháp Streaming Tối Ưu:
1. **Lịch sử tĩnh (Static List)**: Mảng `messages` chứa các tin nhắn cũ được giữ nguyên và dùng vòng lặp render một lần duy nhất.
2. **Buffer động độc lập (Streaming Component)**: Xây dựng một component chuyên biệt `StreamingMessageBubble`. Component này dùng Custom Hook thu hẹp (VD: `useStreamingStore` bằng Zustand) để trực tiếp nhận chuỗi text stream từ WebSocket. Điều này đảm bảo **chỉ re-render một góc nhỏ màn hình** mỗi khi chữ mới (token) được nối (append) vào div.
3. **Auto-Scroll Thông Minh**: Gắn thẻ `<div ref={messagesEndRef} />` ở cuối cùng file. Trong lúc chữ đang chảy về liên tục, sử dụng `element.scrollIntoView({ behavior: 'auto' })` (tránh dùng `smooth` vì gọi liên tục `smooth` trong vài mili-giây sẽ làm kẹt luồng cuộn của trình duyệt).

---

## 5. Task Checklist Khởi Tạo Main Chat

- [ ] Cài đặt các thư viện thiết yếu: `react-markdown`, `react-syntax-highlighter`, `dompurify`, và `zustand` (để quản lý state streaming không re-render).
- [ ] Xây dựng bộ khung Layout chính: `MainLayout.tsx`, `Sidebar.tsx`, `ChatArea.tsx`.
- [ ] Viết Component `AgentStatusIndicator.tsx` tái sử dụng hiệu ứng GSAP từ Timeline 1 để gắn lên Header báo trạng thái.
- [ ] Lắp ráp Component hiển thị tin nhắn `MessageBubble.tsx` tích hợp Markdown parser an toàn chống XSS và các ràng buộc Max Width.
- [ ] Xây dựng Component `ChatInput.tsx` xử lý mượt mà sự kiện Auto-resize Textarea và gán các nút Action (`Stop`, `Clear`).
- [ ] Cài đặt Custom Hook `useChatWebSocket.ts` để quản lý kết nối Tauri WebSocket, xử lý luồng data và nối token cho component buffer stream.
