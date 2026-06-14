import importlib
import inspect
import os
import sys
import logging
from typing import Dict, Type

from backend.infrastructure.plugins.base import BasePlugin
from backend.domain.interfaces.event_bus import IEventBus
from backend.infrastructure.plugins.calendar_plugin import CalendarPlugin
from backend.infrastructure.plugins.web_search_plugin import WebSearchPlugin
from backend.infrastructure.plugins.memory_plugin import MemoryPlugin
from backend.infrastructure.plugins.email_plugin import EmailPlugin
from backend.infrastructure.plugins.flaky_tool_plugin import FlakyToolPlugin
logger = logging.getLogger(__name__)

# Register available plugins here
PLUGIN_REGISTRY = {
    "calendar_plugin": CalendarPlugin,
    "web_search_plugin": WebSearchPlugin,
    "memory_plugin": MemoryPlugin,
    "email_plugin": EmailPlugin,
    "flaky_tool_plugin": FlakyToolPlugin,
}

class EventBusProxy:
    """Proxy bọc IEventBus để kiểm soát quyền publish/subscribe của Plugin."""
    def __init__(self, real_bus: IEventBus, permissions: list[str]):
        self._bus = real_bus
        self._permissions = permissions

    async def publish(self, event) -> None:
        # Giả lập kiểm duyệt quyền
        if "event_publish" not in self._permissions and "all" not in self._permissions:
            raise PermissionError("Plugin does not have event_publish permission")
        await self._bus.publish(event)

    def subscribe(self, event_type: str, handler) -> None:
        if "event_subscribe" not in self._permissions and "all" not in self._permissions:
            raise PermissionError("Plugin does not have event_subscribe permission")
        self._bus.subscribe(event_type, handler)


class PluginManager:
    def __init__(self, event_bus: IEventBus, plugins_dir: str = None):
        self.event_bus = event_bus
        self.plugins_dir = plugins_dir or os.path.dirname(__file__)
        self.loaded_plugins: Dict[str, BasePlugin] = {}

    async def register_plugin(self, plugin_instance: BasePlugin):
        """Đăng ký plugin thủ công (rất hữu ích khi compile bằng PyInstaller)."""
        metadata = plugin_instance.get_metadata()
        name = metadata.get("name", "unknown")
        
        # Inject EventBus proxy
        permissions = metadata.get("permissions", [])
        proxy_bus = EventBusProxy(self.event_bus, permissions)
        plugin_instance.bus = proxy_bus
        
        await plugin_instance.on_load()
        self.loaded_plugins[name] = plugin_instance
        logger.info(f"Manually registered plugin: {name} (v{metadata.get('version', '0.0')})")

    async def discover_and_load(self):
        """Quét thư mục và tự động nạp các subclass của BasePlugin."""
        if self.plugins_dir not in sys.path:
            sys.path.insert(0, self.plugins_dir)
            
        try:
            for filename in os.listdir(self.plugins_dir):
                if filename.endswith(".py") and not filename.startswith("__"):
                    module_name = filename[:-3]
                    try:
                        module = importlib.import_module(module_name)
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if inspect.isclass(attr) and issubclass(attr, BasePlugin) and attr is not BasePlugin:
                                # Không load lại nếu đã được register tay (rất hữu ích cho PyInstaller)
                                plugin_instance = attr()
                                metadata = plugin_instance.get_metadata()
                                name = metadata.get("name", "unknown")
                                if name not in self.loaded_plugins:
                                    await self.register_plugin(plugin_instance)
                    except Exception as e:
                        logger.error(f"Failed to load plugin {module_name}: {e}")
        except FileNotFoundError:
            logger.warning(f"Plugins directory not found at {self.plugins_dir}. Skipping auto-discovery (expected if bundled via PyInstaller).")

    async def start_all(self):
        """Tiêm EventBus Proxy và khởi chạy các Plugin an toàn."""
        for name, plugin in self.loaded_plugins.items():
            try:
                meta = plugin.get_metadata()
                permissions = meta.get("permissions", [])
                proxy_bus = EventBusProxy(self.event_bus, permissions)
                
                await plugin.on_start(proxy_bus)
                logger.info(f"Started plugin: {name}")
            except Exception as e:
                logger.error(f"Plugin {name} crashed on start: {e}")
                # Fault isolation: Một plugin sụp không làm ảnh hưởng app

    async def stop_all(self):
        for name, plugin in self.loaded_plugins.items():
            try:
                await plugin.on_stop()
                logger.info(f"Stopped plugin: {name}")
            except Exception as e:
                logger.error(f"Plugin {name} failed on stop: {e}")

    def get_plugin(self, name: str) -> BasePlugin | None:
        return self.loaded_plugins.get(name)

    def get_available_tools(self) -> list[dict]:
        """Trả về danh sách các tool khả dụng từ tất cả các plugin."""
        tools = []
        for plugin in self.loaded_plugins.values():
            meta = plugin.get_metadata()
            if "tools" in meta:
                tools.extend(meta["tools"])
        return tools

    def _get_setting_sync(self, key: str, default: str = "") -> str:
        try:
            import sqlite3
            from backend.infrastructure.database.encryption import fernet
            if getattr(sys, 'frozen', False):
                appdata_dir = os.getenv('APPDATA', os.path.expanduser("~"))
                db_dir = os.path.join(appdata_dir, "com.aaa.app", "database")
            else:
                db_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "database"))
            
            db_path = os.path.join(db_dir, "app_data.db")
            if not os.path.exists(db_path):
                return default
                
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT setting_value FROM user_settings WHERE setting_key = ?", (key,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                try:
                    return fernet.decrypt(row[0].encode("utf-8")).decode("utf-8")
                except Exception:
                    return row[0]
        except Exception as e:
            logger.error(f"Error reading setting {key} in PluginManager: {e}")
        return default

    async def execute_tool(self, tool_name: str, payload: dict):
        plugin = self.get_plugin(tool_name)
        if not plugin or not hasattr(plugin, 'execute_tool'):
            # Thử tìm theo tool_name trong list tools của tất cả plugin
            for p in self.loaded_plugins.values():
                meta = p.get_metadata()
                for t in meta.get("tools", []):
                    if t.get("name") == tool_name and hasattr(p, 'execute_tool'):
                        plugin = p
                        break
                if plugin:
                    break

        if not plugin:
            raise ValueError(f"Tool plugin '{tool_name}' not found or does not support execute_tool")

        plugin_metadata = plugin.get_metadata()
        plugin_name = plugin_metadata.get("name", "unknown")

        # 1. Kiểm tra trạng thái hoạt động (Active status)
        active_val = self._get_setting_sync(f"plugins.{plugin_name}.active", "true")
        if active_val.lower() == "false":
            raise PermissionError(f"Plugin '{plugin_name}' is disabled. Enable it in settings to use its tools.")

        # 2. Kiểm tra các quyền (Permissions) của plugin
        permissions = plugin_metadata.get("permissions", [])
        for perm in permissions:
            perm_val = self._get_setting_sync(f"plugins.{plugin_name}.permission.{perm}", "true")
            if perm_val.lower() == "false":
                raise PermissionError(f"Authorization Error: Plugin '{plugin_name}' does not have '{perm}' permission.")

        if plugin_name == tool_name:
            return await plugin.execute_tool(payload)
        else:
            return await plugin.execute_tool(tool_name, payload)
