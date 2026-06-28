# Feature: Giao tiếp Ngôn ngữ Tự nhiên & Điều phối Agent (NLP Chat)

## Feature Overview

* **Mục đích**: Xử lý các câu lệnh ngôn ngữ tự nhiên từ người dùng thông qua giao diện Chat. Custom ReAct Agent sẽ đóng vai trò nhạc trưởng (Orchestrator) phân tích ý định, duy trì ngữ cảnh hội thoại, và quyết định khi nào cần gọi các Plugin (Tools) để đáp ứng yêu cầu.
* **Actor**: Người dùng cuối (End User).
* **Business rules**: 
  - Mọi yêu cầu đều phải đi qua `AgentCore`.
  - Kết quả trả về phải nằm trong định dạng JSON chuẩn (IntentDTO, ActionDTO) trước khi xử lý tiếp.
  - Các lỗi phát sinh từ LLM hoặc Plugin không được làm crash hệ thống, thay vào đó hiển thị thông báo thân thiện.
* **Dependencies**: Hybrid LLM Adapter, EventBus, ToolExecutor.

---

### Test Cases

#### Trò chuyện thông thường (Chat cơ bản) <TC-NLP-001>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-NLP-001                                             |
| Test Case       | Kiểm tra luồng chat cơ bản khi người dùng hỏi/đáp hội thoại thông thường. |
| Related Feature | NLP Chat                                              |
| Context         | Hệ thống đã khởi động thành công, người dùng ở màn hình chính. |
| Input Data      | Câu chào: "Xin chào, bạn khỏe không?"                 |
| Expected Output | Agent trả lời bằng ngôn ngữ tự nhiên thân thiện, không kích hoạt công cụ nào. |
| Test Steps      | <ol><li>Mở giao diện Web (localhost:5173).</li><li>Nhập "Xin chào, bạn khỏe không?" vào thanh chat.</li><li>Nhấn Enter hoặc nút Gửi.</li><li>Quan sát phản hồi từ hệ thống.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |

#### Tự động gọi Plugin tạo sự kiện lịch <TC-NLP-002>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-NLP-002                                             |
| Test Case       | Kiểm tra khả năng Agent phân tích ý định và tự động gọi tool `create_calendar_event`. |
| Related Feature | NLP Chat                                              |
| Context         | Database SQLite đã sẵn sàng, EventBus hoạt động bình thường. |
| Input Data      | Câu lệnh: "Đặt lịch cho tôi uống nước vào 5 phút nữa." |
| Expected Output | Agent tự động trích xuất Tool `create_calendar_event`, lưu vào DB thành công và trả về thông báo xác nhận đã đặt lịch. |
| Test Steps      | <ol><li>Nhập câu lệnh đặt lịch vào thanh chat.</li><li>Gửi tin nhắn.</li><li>Kiểm tra thông báo "Thực thi công cụ: create_calendar_event" trên luồng suy luận.</li><li>Kiểm tra nội dung trả lời cuối cùng từ hệ thống.</li><li>(Optional) Kiểm tra bảng `calendar_events` trong cơ sở dữ liệu SQLite.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |

#### LLM trả về cấu trúc JSON bị lỗi <TC-NLP-003>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-NLP-003                                             |
| Test Case       | Kiểm tra cách hệ thống (ReAct Agent) xử lý khi LLM sinh ra output không đúng format JSON (Negative). |
| Related Feature | NLP Chat                                              |
| Context         | Cần thay đổi prompt tạm thời hoặc sử dụng MockLLMAdapter để trả về một chuỗi JSON không hợp lệ (ví dụ: thiếu dấu ngoặc). |
| Input Data      | Chuỗi text rác thay cho JSON: `{"action": "create", ` |
| Expected Output | AgentCore bắt được `JSONDecodeError`, tự động retry hoặc trả lời người dùng: "Hệ thống gặp lỗi trong quá trình suy luận, vui lòng thử lại." |
| Test Steps      | <ol><li>Giả lập LLM sinh JSON lỗi.</li><li>Người dùng gửi một câu hỏi bất kỳ.</li><li>Quan sát log của Backend trên Terminal (hiển thị Error parse).</li><li>Kiểm tra màn hình Chat không bị Crash.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |

#### Plugin báo lỗi thực thi <TC-NLP-004>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-NLP-004                                             |
| Test Case       | Kiểm tra cách ToolExecutor phản hồi lại cho LLM khi một Tool quăng exception (Negative). |
| Related Feature | NLP Chat                                              |
| Context         | Có thể test bằng `flaky_tool_plugin` được tích hợp sẵn. |
| Input Data      | Lệnh: "Hãy dùng flaky tool để test lỗi."              |
| Expected Output | Tool chạy thất bại, báo Exception cho ToolExecutor. LLM nhận được thông báo lỗi từ Tool và thông báo lại cho người dùng bằng ngôn ngữ tự nhiên. |
| Test Steps      | <ol><li>Kích hoạt yêu cầu gọi `flaky_tool_plugin`.</li><li>Kiểm tra log Backend báo lỗi exception.</li><li>Kiểm tra màn hình chat xem AI có thông báo công cụ chạy thất bại không.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |

#### Câu lệnh Chat cực dài <TC-NLP-005>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-NLP-005                                             |
| Test Case       | Gửi nội dung tin nhắn vượt quá giới hạn Token thông thường (Boundary). |
| Related Feature | NLP Chat                                              |
| Context         | Hệ thống hoạt động bình thường. |
| Input Data      | Một chuỗi văn bản dài 10,000 từ.                      |
| Expected Output | Hoặc bị cắt ngắn tự động, hoặc báo lỗi "Tin nhắn quá dài", nhưng không được làm treo Backend. |
| Test Steps      | <ol><li>Copy paste 1 đoạn text cực dài (10,000 từ) vào khung Chat.</li><li>Gửi tin nhắn.</li><li>Quan sát hiệu năng và phản hồi của hệ thống.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |

#### Hủy tiến trình AI (True Full Kill / Stop) <TC-NLP-006>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-NLP-006                                             |
| Test Case       | Xác thực khả năng gián đoạn hoàn toàn luồng sinh text của LLM tại Backend để tiết kiệm tài nguyên. |
| Related Feature | NLP Chat                                              |
| Context         | Backend đang chạy, mạng kết nối ổn định. |
| Input Data      | Lệnh dài: "Hãy viết cho tôi một bài luận 2000 chữ về lịch sử thế giới." |
| Expected Output | Khi nhấn "Stop", Frontend gửi `CANCEL_GENERATION`. Backend ngưng in log ngay lập tức, giải phóng CPU/GPU. Frontend dừng hiển thị text. |
| Test Steps      | <ol><li>Gửi câu lệnh dài yêu cầu AI tạo văn bản.</li><li>Khi AI đang sinh chữ (stream), lập tức nhấn nút "Stop" hình vuông đen.</li><li>Kiểm tra Terminal Backend: Tiến trình sinh chữ phải lập tức báo `Generation cancelled` và ngưng log.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |

#### Nhập liệu bằng giọng nói (Voice Input) <TC-NLP-007>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-NLP-007                                             |
| Test Case       | Kiểm tra chức năng chuyển đổi giọng nói thành văn bản bằng Web Speech API. |
| Related Feature | NLP Chat                                              |
| Context         | Trình duyệt có hỗ trợ Web Speech API (Chrome/Edge). Micro đã được cấp quyền. |
| Input Data      | Bấm nút Micro và nói "Xin chào trợ lý". |
| Expected Output | Giọng nói được nhận diện và tự động điền vào khung chat: "Xin chào trợ lý". |
| Test Steps      | <ol><li>Bấm vào icon Micro bên cạnh ô chat.</li><li>Cấp quyền Micro nếu trình duyệt yêu cầu.</li><li>Nói một câu tiếng Việt hoặc tiếng Anh.</li><li>Chờ 1-2 giây xem chữ có hiển thị lên ô chat không.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |

#### Thư viện Mẫu lệnh (Prompt Library) <TC-NLP-008>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-NLP-008                                             |
| Test Case       | Kiểm tra tính năng chọn nhanh các kịch bản có sẵn. |
| Related Feature | NLP Chat                                              |
| Context         | Đang ở màn hình Chat trống (New Conversation). |
| Input Data      | Bấm icon Tia sét (Zap) -> Chọn mẫu "Thêm lịch mới". |
| Expected Output | Khung chat tự động điền mẫu: "Hãy lên lịch cho sự kiện [Tên sự kiện] vào lúc [Thời gian]...". |
| Test Steps      | <ol><li>Mở một đoạn chat mới.</li><li>Bấm vào icon Tia sét (Zap) góc trái ô chat.</li><li>Chọn một mẫu lệnh trong danh sách dropdown.</li><li>Kiểm tra nội dung ô chat có được điền đúng template không.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |

#### Ghi nhớ thông tin cá nhân (Memory Plugin) <TC-NLP-009>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-NLP-009                                             |
| Test Case       | Kiểm tra khả năng lưu trữ thông tin cá nhân vào trí nhớ dài hạn. |
| Related Feature | NLP Chat                                              |
| Context         | Hệ thống đã khởi động thành công. |
| Input Data      | Câu lệnh: "Sở thích của tôi là lập trình Python, hãy nhớ điều này." |
| Expected Output | Agent tự động gọi Tool lưu bộ nhớ và trả về xác nhận. Sau đó, khi hỏi "Tôi thích ngôn ngữ nào?", Agent truy xuất đúng "Python". |
| Test Steps      | <ol><li>Nhập câu lệnh ghi nhớ vào thanh chat.</li><li>Nhấn Gửi.</li><li>Kiểm tra thông báo AI xác nhận đã nhớ.</li><li>Bắt đầu cuộc trò chuyện mới hoặc hỏi luôn "Tôi thích ngôn ngữ nào?".</li><li>Xác nhận câu trả lời có chứa thông tin đã lưu.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |

#### Quản lý công việc (Task Plugin) <TC-NLP-010>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-NLP-010                                             |
| Test Case       | Kiểm tra khả năng tạo công việc và gọi tool liên tiếp (Chain of Thought). |
| Related Feature | NLP Chat                                              |
| Context         | Database SQLite đã sẵn sàng. |
| Input Data      | Câu lệnh: "Thêm việc mua sắm, sau đó hiển thị toàn bộ task hiện có." |
| Expected Output | Agent gọi liên tiếp 2 tool: `create_task` và `list_tasks`. Sau đó hiển thị danh sách task đã cập nhật cho người dùng. |
| Test Steps      | <ol><li>Nhập câu lệnh tạo task và liệt kê vào thanh chat.</li><li>Gửi tin nhắn.</li><li>Kiểm tra log luồng suy luận xem Agent có gọi 2 tool không.</li><li>Xác nhận hiển thị UI trả về kết quả đúng.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |

#### Tra cứu Web (Web Search Plugin) <TC-NLP-011>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-NLP-011                                             |
| Test Case       | Kiểm tra khả năng kết nối mạng để tìm kiếm thông tin theo thời gian thực. |
| Related Feature | NLP Chat                                              |
| Context         | Máy tính có kết nối Internet ổn định. |
| Input Data      | Câu lệnh: "Giá vàng hôm nay là bao nhiêu?" |
| Expected Output | Agent gọi tool `web_search` để lấy dữ liệu mới nhất và tổng hợp câu trả lời cho người dùng. |
| Test Steps      | <ol><li>Nhập câu lệnh hỏi thông tin cập nhật vào thanh chat.</li><li>Nhấn Gửi.</li><li>Kiểm tra xem Agent có hiển thị đang thực thi tool tìm kiếm hay không.</li><li>Đọc câu trả lời xem có chứa thông tin mới không (không bị hallucinate).</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |

#### Thiếu tham số (Missing Arguments Edge Case) <TC-NLP-012>

| Field           | Content                                                |
| --------------- | ------------------------------------------------------ |
| Test Case ID    | TC-NLP-012                                             |
| Test Case       | Kiểm tra khả năng bắt lỗi thiếu thông tin, AI KHÔNG được bịa đặt tham số (Negative). |
| Related Feature | NLP Chat                                              |
| Context         | Hệ thống hoạt động bình thường. |
| Input Data      | Câu lệnh: "Tạo lịch cuộc họp." (Cố tình thiếu ngày giờ). |
| Expected Output | Agent không gọi tool `create_calendar_event` ngay mà sẽ trả lời yêu cầu người dùng cung cấp thêm thời gian. |
| Test Steps      | <ol><li>Nhập câu lệnh mập mờ thiếu ngày giờ vào thanh chat.</li><li>Gửi tin nhắn.</li><li>Kiểm tra luồng xử lý: Tool không được phép kích hoạt khi validate schema thất bại.</li><li>Xác nhận AI phản hồi yêu cầu bổ sung thông tin.</li></ol> |
| Actual Output   |                                                        |
| Result          |                                                        |
