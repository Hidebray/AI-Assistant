import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.infrastructure.plugins.manager import PluginManager

logger = logging.getLogger(__name__)

class IngestionWorker:
    def __init__(self, plugin_manager: PluginManager):
        self.plugin_manager = plugin_manager
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def fetch_data_task(self):
        """Hàm job được gọi định kỳ để kích hoạt các Plugin sync."""
        logger.info("Background Worker: Bắt đầu chu kỳ quét dữ liệu ngầm...")
        # Lẽ ra ở đây sẽ gọi một event hoặc loop qua plugin
        # Tuy nhiên Plugin tự có vòng lặp hoặc Worker sẽ gọi plugin logic
        # Hiện tại IngestionWorker sẽ giả lập việc phát tín hiệu cho các Plugin
        
        # Fake task logic
        await asyncio.sleep(1)
        logger.info("Background Worker: Hoàn thành quét dữ liệu.")

    def start(self):
        if self.is_running:
            return
        
        self.is_running = True
        # Lập lịch chạy mỗi 15 phút (900 giây), test để 60 giây
        self.scheduler.add_job(
            self.fetch_data_task,
            trigger=IntervalTrigger(seconds=60),
            id='fetch_data_job',
            name='Fetch external data via Plugins',
            replace_existing=True
        )
        self.scheduler.start()
        logger.info("IngestionWorker started via APScheduler.")

    def stop(self):
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("IngestionWorker stopped.")
