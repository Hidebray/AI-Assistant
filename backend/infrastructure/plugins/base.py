from abc import ABC, abstractmethod
from typing import Dict, Any
from backend.domain.interfaces.event_bus import IEventBus

class BasePlugin(ABC):
    """Giao diện chuẩn định nghĩa vòng đời cho mọi Plugin."""

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Trả về siêu dữ liệu của Plugin để Registry quản lý.
        Ví dụ: {'name': 'calendar_sync', 'version': '1.0.0', 'permissions': ['db_read', 'network']}
        """
        pass

    @abstractmethod
    async def on_load(self) -> None:
        """Được gọi khi PluginManager tìm thấy và nạp plugin vào bộ nhớ."""
        pass

    @abstractmethod
    async def on_start(self, event_bus: IEventBus) -> None:
        """Được gọi khi Plugin được lệnh khởi chạy. Nơi inject EventBus."""
        pass

    @abstractmethod
    async def on_stop(self) -> None:
        """Được gọi khi người dùng tắt Plugin hoặc ứng dụng dừng."""
        pass
