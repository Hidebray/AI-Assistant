# Đặc tả Hệ thống Plugin (Plugin Registry Specification)

Tài liệu này đặc tả kiến trúc mở rộng theo mô hình **Microkernel** của dự án Autonomous AI Assistant (AAA). Lõi hệ thống (Core) được giữ ở mức siêu nhẹ và tối giản, toàn bộ các tính năng tương tác với thế giới bên ngoài (Email, Lịch, Trình duyệt, API bên thứ 3) đều được đóng gói dưới dạng các Plugins chạy độc lập.

## 1. Ràng Buộc Kiến Trúc (Architectural Constraints)

1. **Độc lập hoàn toàn (Decoupled)**: Plugin tuyệt đối không được import hay can thiệp trực tiếp vào logic của Lõi (AgentCore) hoặc các Plugin khác. Mọi giao tiếp hai chiều đều phải được thực hiện thông qua việc Publish/Subscribe các gói tin trên `IEventBus`.
2. **Cách ly lỗi (Fault Isolation)**: Mỗi Plugin được cấp phát chạy trong một luồng bất đồng bộ (`asyncio.Task`) riêng biệt và được bọc khối try-catch toàn diện. Một Plugin bị crash (ví dụ: mất kết nối API, lỗi parse JSON) sẽ chỉ bị vô hiệu hóa (disabled), tuyệt đối không được kéo theo sự sụp đổ của tiến trình ứng dụng chính.
3. **Vòng đời Động (Dynamic Lifecycle)**: Hệ thống hỗ trợ cơ chế nạp động (Dynamic Loading) qua thư viện `importlib`, cho phép Load, Start, Stop các plugin ngay tại Runtime mà không cần khởi động lại toàn bộ phần mềm.

---

## 2. Đặc Tả Giao Diện Plugin (Plugin Interface)

Mọi Plugin được phát triển cho AAA đều bắt buộc phải kế thừa và triển khai các phương thức từ lớp trừu tượng `BasePlugin`.

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class BasePlugin(ABC):
    """Giao diện chuẩn định nghĩa vòng đời cho mọi Plugin."""

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Trả về siêu dữ liệu của Plugin để Registry quản lý.
        Ví dụ: {'name': 'calendar_plugin', 'version': '1.0.0', 'permissions': ['db_read', 'network'], 'config_schema': {}}
        """
        pass

    @abstractmethod
    async def on_load(self) -> None:
        """Được gọi khi PluginManager tìm thấy và nạp plugin vào bộ nhớ. Nơi khởi tạo cấu hình, đọc token."""
        pass

    @abstractmethod
    async def on_start(self, event_bus: 'IEventBus') -> None:
        """Được gọi khi Plugin được lệnh khởi chạy. Nơi inject EventBus và đăng ký Subscribe các sự kiện."""
        pass

    @abstractmethod
    async def on_stop(self) -> None:
        """Được gọi khi người dùng tắt Plugin hoặc ứng dụng dừng. Nơi dọn dẹp bộ nhớ, ngắt kết nối an toàn."""
        pass
```

---

## 3. Trung Tâm Quản Lý (PluginManager)

`PluginManager` là linh hồn của kiến trúc Microkernel, đóng vai trò như một người điều phối không can thiệp vào nghiệp vụ.

### Logic Hoạt Động Cốt Lõi:
1. **Discovery (Quét tự động)**: Khi ứng dụng backend khởi chạy, `PluginManager` duyệt qua cây thư mục `src/plugins/`. Nó dùng `importlib` kết hợp `inspect` để tìm các class kế thừa từ `BasePlugin`.
2. **Registration (Đăng ký & Kiểm duyệt)**: Đọc thông tin từ `get_metadata()`. Xác minh xem Plugin có yêu cầu quyền hạn hợp lệ hay không.
3. **Dependency Injection**: Khi nhận lệnh start, `PluginManager` lặp qua danh sách plugin đã duyệt và gọi `plugin.on_start(event_bus)`. `event_bus` được tiêm vào chính là cầu nối duy nhất của Plugin với Lõi.
4. **Fault Recovery**: Toàn bộ vòng đời gọi hàm của Plugin được bao bọc bởi `try-except`. Nếu `on_start` hoặc tiến trình ngầm của Plugin ném Exception, `PluginManager` sẽ bắt lấy, chuyển state của Plugin sang `Error`, và xuất một `SystemEvent` báo cáo lên UI, Lõi AI vẫn hoạt động bình thường với các Plugin khác.

---

## 4. Cơ Chế Bảo Mật & Quyền Hạn (Sandboxing / Permissions)

Mặc dù là Local App, việc giới hạn thẩm quyền của Plugin là cực kỳ cần thiết để phòng chống các Plugin của bên thứ 3 (nếu có) phá hoại dữ liệu.
- **Khai báo Manifest**: `get_metadata()` trả về mảng `permissions` (vd: `network`, `read_db`, `call_llm`).
- **Kiểm soát Event Bus**: `PluginManager` không truyền trực tiếp biến `event_bus` nguyên bản cho Plugin, mà truyền một class bọc (Proxy Wrapper). Proxy này sẽ đối chiếu `permissions`.

---

## 5. Ví Dụ Minh Họa Một Plugin (Plugin Template)

Dưới đây là mã giả (Pseudo-code) cho `CalendarPlugin`, minh họa cơ chế hoạt động lên lịch và nhận lệnh từ Lõi thông qua Event Bus.

```python
from domain.events import AgentActionCompletedEvent, NewCalendarEvent
from infrastructure.plugin_base import BasePlugin

class CalendarPlugin(BasePlugin):
    async def on_start(self, event_bus):
        self.bus = event_bus
        self.bus.subscribe("Agent.ActionCompleted", self.handle_action_completion)
        print("Calendar Plugin started.")

    def get_metadata(self) -> dict:
        return {
            "name": "In-app Calendar",
            "version": "1.0",
            "capabilities": ["calendar_write"]
        }

    def execute_tool(self, tool_name: str, args: dict):
        if tool_name == "create_calendar_event":
            # Ghi vào SQLite thay vì gọi API bên thứ ba
            print("Event created in local DB")
            
    async def handle_action_completion(self, event: AgentActionCompletedEvent):
        if "calendar" in str(event.result_data).lower():

    async def on_stop(self):
        # Dọn dẹp cờ vòng lặp
        self.is_running = False
```

---

## 6. Task Checklist Khởi Tạo Plugin Registry

- [x] Viết module `infrastructure/plugins/base.py` chứa abstract class `BasePlugin`.
- [x] Xây dựng class `PluginManager` tại `infrastructure/plugins/manager.py` với logic quét thư mục tự động qua `importlib`.
- [x] Cài đặt cơ chế Catch-All Exception trong lifecycle của `PluginManager` để đảm bảo Fault Isolation.
- [x] Tích hợp Giao diện UI cấu hình Plugin (Settings), bổ sung `config_schema: {"oauth": True}` để cho phép kích hoạt OAuth từ giao diện đối với Google API.
- [x] Xây dựng các plugin thực tế: `CalendarPlugin`, `WebSearchPlugin`, `MemoryPlugin`, và `EmailPlugin` (sử dụng Gmail API).
