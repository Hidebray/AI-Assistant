# Feature: Hybrid LLM Fallback (Cơ chế suy luận dự phòng)

## Feature Overview

* **Mục đích**: Đảm bảo hệ thống AAA luôn có khả năng suy luận ngay cả khi mất mạng internet hoặc hết quota API. `HybridLLMAdapter` sẽ tự động chuyển đổi qua lại giữa Cloud LLM (OpenAI/Gemini) và Local LLM (Ollama/Llama 3) dựa trên trạng thái kết nối.
* **Actor**: HybridLLMAdapter, AgentCore.
* **Business rules**: 
  - Thử dùng Cloud LLM đầu tiên (nếu có API Key).
  - Nếu gặp lỗi Timeout, RateLimit, NetworkError -> Tự động chuyển sang Local LLM (Ollama).
  - Cả Cloud và Local đều chết -> Trả về lỗi thân thiện.
* **Dependencies**: `NetworkMonitor`, Ollama Server, OpenAI API.

---

### Test Cases

#### Tự động Fallback từ Cloud sang Local khi rớt mạng <TC-HYB-001>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-HYB-001                                             |
| Test Case       | Giả lập rớt mạng để API Cloud bị lỗi, kiểm tra xem hệ thống có tự rẽ nhánh sang Local Model không (Positive). |
| Related Feature | Hybrid LLM                                             |
| Context         | Ollama đang chạy ngầm localhost. Có kết nối mạng. |
| Input Data      | Gửi câu hỏi "Bạn là ai?" sau khi ngắt kết nối Wifi/Ethernet. |
| Expected Output | Hệ thống bị delay 1 lúc (chờ Timeout từ Cloud), sau đó Agent vẫn trả lời bình thường bằng trí tuệ của Local Llama 3 (nhận diện qua văn phong hoặc log terminal). |
| Test Steps      | <ol><li>Ngắt kết nối mạng của máy tính.</li><li>Vào UI chat hỏi 1 câu bất kỳ.</li><li>Kiểm tra log Backend có dòng "Cloud API Failed. Fallback to Local LLM".</li><li>Xác nhận UI hiển thị câu trả lời hoàn chỉnh.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |

#### Hệ thống sụp đổ (Cả Cloud và Local đều chết) <TC-HYB-002>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-HYB-002                                             |
| Test Case       | Tắt cả hai môi trường để ép lỗi về AgentCore (Negative). |
| Related Feature | Hybrid LLM                                             |
| Context         | Ngắt kết nối mạng VÀ Tắt hoàn toàn service Ollama (`taskkill /F /IM ollama.exe`). |
| Input Data      | Gõ "Chào bạn". |
| Expected Output | UI hiển thị thông báo lỗi thân thiện: "Hệ thống AI hiện không khả dụng do mất kết nối mạng và Local LLM chưa được bật." (Hoặc nội dung tương đương), không bị treo loading vĩnh viễn. |
| Test Steps      | <ol><li>Tắt Wifi.</li><li>Tắt Ollama.</li><li>Gửi tin nhắn chat.</li><li>Quan sát UI sau khi Timeout.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |

#### Ưu tiên Cloud LLM khi có mạng <TC-HYB-003>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-HYB-003                                             |
| Test Case       | Xác nhận Adapter luôn ưu tiên gọi Cloud LLM nếu cấu hình hợp lệ (Positive). |
| Related Feature | Hybrid LLM                                             |
| Context         | Mạng ổn định, có API Key OpenAI hợp lệ, Ollama đang chạy. |
| Input Data      | Gõ "Hãy kể 1 câu chuyện vui". |
| Expected Output | Log Backend ghi nhận gọi thành công OpenAI API, không hề trigger Ollama. Tốc độ phản hồi cực nhanh. |
| Test Steps      | <ol><li>Đảm bảo mạng ổn định.</li><li>Nhập text và gửi.</li><li>Kiểm tra Terminal xem luồng chạy đi vào nhánh nào.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |
