# Đặc tả Cổng Kết Nối Trí Tuệ Nhân Tạo (LLM Integration Spec)

Tài liệu này đặc tả kiến trúc tầng Giao tiếp với Mô hình Ngôn ngữ Lớn (LLM) cho dự án Autonomous AI Assistant (AAA). Hệ thống áp dụng triết lý thiết kế LLM-Agnostic, cho phép chuyển đổi mượt mà giữa các mô hình đám mây (Cloud LLM) và cục bộ (Local LLM), đồng thời áp đặt kỷ luật nghiêm ngặt về định dạng đầu ra thông qua Structured Outputs.

---

## 1. Cấu Trúc LLM Adapter (HybridLLMAdapter)

Để tuân thủ thiết kế Ports & Adapters, Lõi hệ thống sẽ giao tiếp với LLM thông qua interface `ILLMAdapter`. Lớp cài đặt cụ thể tại hạ tầng là `HybridLLMAdapter` sẽ bọc toàn bộ logic gọi API.

### 1.1. Kiến Trúc Bao Bọc (Wrapper Architecture)
- **Thư viện lõi**: Sử dụng `openai` Python SDK làm client tiêu chuẩn (do hầu hết các Local LLM server như Ollama hay LM Studio đều tương thích chuẩn API của OpenAI).
- **Chuyển đổi linh hoạt (Hybrid)**: Bằng cách cho phép thay đổi động biến `base_url` và `api_key` trong phần Cài đặt của User, hệ thống có thể kết nối tới `api.openai.com`, `api.gemini.com` (thông qua adapter/litellm) hoặc trỏ về `http://localhost:11434/v1` (Ollama) một cách trong suốt.

### 1.2. Cơ Chế Xử Lý Lỗi (Resilience)
Sử dụng thư viện `tenacity` để xử lý các vấn đề về mạng hoặc giới hạn API (Rate Limit), đảm bảo tính ổn định tối đa.
```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import RateLimitError, APITimeoutError

class HybridLLMAdapter(ILLMAdapter):
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APITimeoutError))
    )
    def generate_response(self, messages: list, response_format: type[BaseModel] = None) -> Any:
        # Logic gọi LLM SDK với timeout và ép kiểu Structured Output...
        pass
```

---

## 2. Đặc Tả Hệ Thống Prompt (System Prompts)

Prompt được quản lý như một thành phần cấu hình tách biệt khỏi mã nguồn Python để dễ dàng điều chỉnh.

### 2.1. Cấu Trúc Thư Mục Prompt
```text
infrastructure/prompts/
├── core/
│   ├── react_agent.prompt.j2        # Prompt chính điều phối chu trình ReAct
│   ├── context_assembler.py         # Lắp ráp ngữ cảnh động
└── tools/
    └── summarize.prompt.j2
```
*Ghi chú: Sử dụng Jinja2 (`.j2`) để render template động kết hợp với các biến ngữ cảnh (context variables).*

### 2.2. Ví dụ System Prompt (Dành cho ReAct Agent)
```text
You are Autonomous AI Assistant.
Analyze the user's input and <CONTEXT> to determine the next best action.

AVAILABLE CAPABILITIES:
- Web Search
- Calendar Event Creation
- Email Reading

RULES:
1. You MUST output ONLY valid JSON matching the ActionDTO schema.
2. If you need a tool, specify `action_type="tool_call"`.
3. If you can answer directly, specify `action_type="direct_response"`.

CURRENT CONTEXT:
{{ current_context }}
```

---

## 3. Đặc Tả Cơ Chế Ép Kiểu Đầu Ra (Structured Output Schema)

Hệ thống TUYỆT ĐỐI KHÔNG parse chuỗi string thô bằng Regex. Mọi kết quả tư duy định hướng của LLM phải tuân theo JSON Schema được định nghĩa bằng Pydantic, ép buộc qua tính năng **Structured Outputs** (nếu dùng OpenAI/Gemini) hoặc **JSON Mode / Tool Calling** (nếu dùng Local LLM).

### Ví dụ: Hành Động AI (ActionDTO)
```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class ActionDTO(BaseModel):
    rationale: str = Field(..., description="Suy luận ngắn gọn lý do chọn hành động này")
    action_type: str = Field(..., description="Loại hành động: 'tool_call', 'direct_response', 'clarification'")
    tool_name: Optional[str] = Field(None, description="Tên công cụ cần gọi nếu có")
    tool_args: Optional[Dict[str, Any]] = Field(None, description="Tham số truyền cho tool")
    response_content: Optional[str] = Field(None, description="Câu trả lời trực tiếp cho người dùng")
```
*Khi gọi LLM, Adapter sẽ truyền `response_format=ActionDTO` để bảo đảm JSON trả về map chính xác 1-1 thành Object.*

---

## 4. Chiến Lược Quản Lý Ngữ Cảnh (Memory & Token Management)

Vì Context Window của LLM (đặc biệt là các mô hình cục bộ) có giới hạn chặt chẽ (vd: 8k - 32k tokens), Lõi AI sử dụng cơ chế **Lắp ráp ngữ cảnh động (Dynamic Context Assembly)**.

### 4.1. Quy trình Lắp Ráp `messages` Array
1. **[0] System Prompt**: Chứa Persona và System Instructions.
2. **[1] Long-term Context**: Lõi AI truy vấn `MemoryAggregate` (bảng `memory_nodes`) để lấy ra top thông tin cá nhân/sở thích liên quan nhất, nhét vào thẻ `<CONTEXT>`.
3. **[2..N-1] Short-term Memory**: Lịch sử chat ngắn hạn, chỉ giữ lại từ 5-10 lượt hội thoại gần nhất.
4. **[N] User Input**: Lời thoại hoặc tín hiệu mới nhất.

### 4.2. Cơ Chế Cắt Tỉa & Tóm Tắt (Truncation & Summarization)
- **Token Estimator**: Sử dụng thư viện `tiktoken` (hoặc bộ đếm độ dài chuỗi tương đối) để tính toán số lượng Token xấp xỉ của mảng `messages` trước khi ném lên Adapter.
- **Auto-Summarization**: Nếu tổng token vượt quá ngưỡng an toàn (vd: 80% Context Window limit), hệ thống lập tức kích hoạt luồng ngầm sử dụng prompt tóm tắt (`summarize.prompt.j2`). Luồng này sẽ nén toàn bộ nội dung lịch sử chat cũ thành một đoạn văn súc tích, lưu lại dưới dạng `System` message và giải phóng Token cho các lượt thoại mới.

### 4.3. Kiến Trúc Ngôn Ngữ (Language Resolution Architecture)
Toàn bộ "Dữ liệu ẩn" (Backend Plugins, AI Tool Schemas, Context) được dịch 100% sang Tiếng Anh để tối ưu hiệu suất LLM. Tuy nhiên, ngôn ngữ AI dùng để giao tiếp với người dùng được quyết định dựa trên mô hình **Tháp Ưu Tiên 4 Tầng (4-Level Priority Cascade)**:
1. **Highest Priority**: Yêu cầu trực tiếp của người dùng trong tin nhắn hiện tại (VD: "Dịch câu trên sang tiếng Nhật").
2. **High Priority**: Ngôn ngữ được sử dụng trong tin nhắn gần nhất của người dùng.
3. **Medium Priority**: Nếu tin nhắn gần nhất quá ngắn/không rõ ràng ("OK", "123"), AI phân tích và dùng ngôn ngữ chính của toàn bộ lịch sử hội thoại hiện tại.
4. **Fallback Priority**: Nếu tất cả các điều kiện trên thất bại, AI bắt buộc sử dụng Ngôn Ngữ Hệ Thống (System Language - truyền từ Frontend UI Settings).

---

## 5. Task Checklist Khởi Tạo LLM Integration

- [ ] Cài đặt gói `openai`, `tenacity`, `jinja2`, và `tiktoken`.
- [ ] Thiết lập thư mục `infrastructure/llm/` và tạo class `HybridLLMAdapter` triển khai từ `ILLMAdapter`.
- [ ] Tích hợp tính năng Structured Outputs thông qua Pydantic schema vào hàm call API.
- [ ] Xây dựng module `TokenEstimator` hỗ trợ ước lượng độ dài Token nhanh cục bộ.
- [ ] Xây dựng module `ContextAssembler` chịu trách nhiệm lắp ghép System Prompt, RAG Context và Lịch sử trò chuyện trước khi gửi.
- [ ] Tạo thư mục `infrastructure/prompts/` và viết các file `.j2` template đầu tiên cho `Planner` và `DecisionEngine`.
