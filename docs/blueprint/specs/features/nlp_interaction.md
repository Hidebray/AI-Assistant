# Đặc tả Nghiệp vụ Tương tác Ngôn ngữ & Trí nhớ AI (NLP & Memory Specs)

Tài liệu này quy định cách thức Trợ lý AI (AAA) thấu hiểu ngôn ngữ tự nhiên của người dùng và phương pháp quản lý giới hạn Token nghiêm ngặt thông qua cơ chế phân tách Trí nhớ Ngắn hạn (Short-term) và Trí nhớ Dài hạn (Long-term). Toàn bộ dữ liệu trí nhớ đều được mã hóa cục bộ và tuân thủ nguyên tắc Privacy-First, gắn liền với `user_id` hiện tại.

---

## 1. User Stories (Câu Chuyện Người Dùng)

- **US01 (Hiểu ngữ cảnh mờ)**: *Là một người dùng thường xuyên*, tôi muốn AI có thể hiểu được các đại từ nhân xưng ("nó", "việc đó", "chọn cái thứ 2") dựa trên các câu hội thoại ngay trước đó, *để* tôi có thể chat tự nhiên như người thật mà không phải nhắc lại bối cảnh dài dòng.
- **US02 (Ghi nhớ tự động)**: *Là một người bận rộn*, tôi muốn AI tự động lắng nghe và nhớ được thói quen cá nhân (VD: "Tôi không ăn được cay", "Tôi thích dùng bảng Markdown để xem dữ liệu"), *để* các phân tích và câu trả lời sau này luôn được cá nhân hóa hoàn hảo mà tôi không cần phải cấu hình tay.
- **US03 (Yêu cầu Quên/Xóa - Right to be forgotten)**: *Là một người dùng quan tâm đến tính bảo mật*, tôi muốn có khả năng ra lệnh "Hãy quên đi toàn bộ ý tưởng về dự án X", *để* AI vĩnh viễn xóa bỏ các facts đó khỏi bộ não và không bao giờ đề cập lại các thông tin nhạy cảm này nữa.

---

## 2. Luồng Tương Tác Chat (Chat Interaction Flow)

Mọi tin nhắn của User không được ném thẳng tới LLM ngay lập tức mà phải trải qua một "Đường ống" (Cognitive Pipeline) 6 bước:

1. **Tiếp nhận & Làm sạch (Ingestion)**: User nhấn gửi tin. Frontend đẩy qua luồng WebSocket. Lõi Python nhận text, xác minh Token hợp lệ, trích xuất `user_id` và `conversation_id`.
2. **Truy hồi Ngữ cảnh (Context Retrieval)**:
   - *Ngắn hạn*: Rút trích $K$ tin nhắn gần nhất trong bảng `messages`.
   - *Dài hạn*: Chạy thuật toán Vector Search nhẹ (hoặc Keyword BM25) trong bảng `memory_nodes` để tìm các sự kiện (Facts) liên quan mật thiết đến câu hỏi mới của User.
3. **Lắp ráp Prompt (Prompt Assembly)**: Bơm toàn bộ Ngữ cảnh (Ngắn hạn + Dài hạn) vào `System Prompt Template` (Jinja2) để định hình góc nhìn cho AI trước khi nó trả lời. Quá trình này sẽ sử dụng biến `system_language` và kích hoạt **Tháp Ưu Tiên 4 Tầng (4-Level Priority Cascade)** để xác định ngôn ngữ phản hồi.
4. **Gọi LLM (Execution)**: Đẩy gói lệnh cho `HybridLLMAdapter` (OpenAI/Gemini/Ollama) thực thi.
5. **Phản hồi Tức thời (WebSocket Streaming)**: Trả từng ký tự token về Frontend React để render hiệu ứng mượt mà. Đảm bảo ngôn ngữ trả về nhất quán với quy tắc ngôn ngữ.
6. **Lưu trữ & Rút trích ngầm (Memory Consolidation)**: 
   - Lưu nguyên văn câu hỏi/trả lời vào bảng `messages` (Dùng cho UI).
   - *Background Task*: Kick-off một thread chạy ngầm phân tích lại đoạn hội thoại vừa xong để tìm xem có **"Thông tin cốt lõi nào có giá trị lâu dài"** không. Nếu có, tóm tắt nó thành các `Nodes` (Ví dụ: `User_Allergy: Đậu phộng`) và đẩy vào bảng `memory_nodes`.

---

## 3. Kiến trúc Đa ngôn ngữ (Language Resolution Architecture)

Để tối ưu hóa độ chính xác cho AI khi tư duy (Tool Calling, suy luận logic) trong khi vẫn đảm bảo trải nghiệm giao tiếp bản địa với người dùng, hệ thống sử dụng kiến trúc chuẩn hóa ngôn ngữ 2 lớp:

1. **Lớp Lõi / Dữ liệu Ẩn (English-First Core)**: Toàn bộ JSON Schemas, plugin tool descriptions, log lỗi, và thông báo trạng thái ngầm được viết bằng tiếng Anh. Điều này tăng cường hiệu suất của LLM (thường được huấn luyện mạnh trên kho dữ liệu tiếng Anh).
2. **Tháp Ưu Tiên 4 Tầng (4-Level Language Priority Cascade)**: Áp dụng trực tiếp trong System Prompt, AI quyết định ngôn ngữ trò chuyện dựa trên:
   - **Tầng 1 (Cao nhất)**: Yêu cầu trực tiếp của người dùng trong tin nhắn hiện tại (VD: "Hãy giải thích bằng tiếng Pháp").
   - **Tầng 2**: Ngôn ngữ được phát hiện ở tin nhắn gần nhất của người dùng.
   - **Tầng 3**: Ngôn ngữ chủ đạo của toàn bộ cuộc hội thoại hiện tại.
   - **Tầng 4 (Mặc định)**: System Language (ngôn ngữ cấu hình ở UI) truyền thông qua biến `language` trong Event Bus.

---

## 4. Quy Tắc Quản Lý Trí Nhớ (Memory Management Rules)

Vì giới hạn Context Window của LLM (thường từ 8K đến 32K Token), nếu cứ nhồi nhét vô hạn lịch sử chat thì request sẽ bị từ chối hoặc AI sẽ bị "ngáo" (ảo giác - Hallucination).

### 3.1. Trí Nhớ Ngắn Hạn (Working Memory) & Hybrid Auto-Summarization
- **Định nghĩa**: Bối cảnh đang diễn ra trong cuộc hội thoại hiện tại.
- **Quy tắc đếm Token (Token Counting)**: Sử dụng `tiktoken` để kiểm soát dung lượng của ngữ cảnh. Hard-limit thường được đặt ở mức 3000 tokens.
- **Mô hình Hybrid Memory (Lai)**: 
  - Lưu 2 cột `summary_content` và `last_summarized_message_id` vào Database.
  - Khi load context, hệ thống nạp: `[summary_content]` + `[Các tin nhắn MỚI sau mốc last_summarized_message_id]`.
  - Nếu tổng tokens <= 3000: Không làm gì cả, LLM trả lời ngay lập tức.
  - Nếu tổng tokens > 3000: Kích hoạt ngầm một phiên tóm tắt, LLM sẽ nhận `[summary_content (cũ)]` + `[Các tin nhắn MỚI]` để sinh ra một bản `summary_content (mới)`. Bản mới này được ghi đè vào CSDL và cập nhật lại mốc `last_summarized_message_id`.
  - Lợi ích: Tin nhắn cũ của User **không bao giờ bị xóa** khỏi DB nên UI vẫn hiển thị đầy đủ lịch sử, nhưng Backend chỉ tốn cực ít token cho LLM vì không cần phải nhồi toàn bộ lịch sử hay tóm tắt đi tóm tắt lại nhiều lần.

### 3.2. Trí Nhớ Dài Hạn (Semantic Memory)
- **Định nghĩa**: Các "Sự thật" (Facts), "Mối quan hệ" (Relations) hoặc "Sở thích" (Preferences) được chắt lọc và sống vĩnh viễn ở bảng `memory_nodes`.
- **Cơ chế Quên lãng (Memory Decay)**: Con người không nhớ mọi thứ, AI cũng vậy.
  - Mỗi Node có trường `last_accessed` (Thời điểm truy cập cuối) và `weight` (Mức độ quan trọng, thang điểm 1-100).
  - Khi một Node được gọi ra xài, `weight` của nó tăng lên (AI củng cố trí nhớ).
  - **Cronjob hàng ngày**: Mỗi ngày, Lõi hệ thống lướt qua toàn bộ Nodes và trừ đi một lượng `weight` nhỏ. Nếu một thông tin không được đả động tới trong 30 ngày và `weight` rớt xuống mức đáy (< 10), Node đó sẽ bị đánh dấu `is_archived = True` và chìm vào quên lãng (không được đưa vào Prompt nữa).

### 3.3. Xóa Bỏ Chủ Động (Explicit Forgetting)
Nếu user ra lệnh rõ ràng: *"Hãy xóa toàn bộ ký ức về Sở thích A"*. LLM sẽ gọi ra một JSON Tool/Function là `delete_memory(query)`. Hệ thống tìm và hard-delete hoàn toàn các Node liên quan khỏi SQLite, đảm bảo tuyệt đối quyền riêng tư.

---

## 5. Task Checklist Triển Khai Xử Lý Ngữ Cảnh (Lõi AI)

- [x] Lập trình thuật toán Hybrid Memory (đếm token bằng `tiktoken`) tại module `ChatWorker` để cắt tỉa bớt mảng lịch sử trước khi bơm cho LLM.
- [x] Viết luồng `Auto-Summarization`: Hàm tự động kích hoạt LLM thu gọn các tin nhắn cũ bằng chiến lược Lai (Hybrid) khi Context Window chạm ngưỡng 3000 tokens.
- [x] Xây dựng Background Task `MemoryConsolidator`: Chạy ngầm rút trích Facts/Preferences từ tin nhắn người dùng và lưu vào `memory_nodes`.
- [x] Viết Job `MemoryDecayWorker`: Cronjob `APScheduler` chạy 1 lần/giờ để trừ dần trọng số (weight) của trí nhớ dài hạn và xóa các node rác.
- [x] Phát triển công cụ (Tool Use) `forget_memory` (qua `MemoryPlugin`) để LLM có thể gọi API xóa hẳn Node trong DB khi người dùng ra lệnh.
