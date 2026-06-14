import asyncio
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from backend.infrastructure.database.session import db_manager
from backend.infrastructure.database.models import MemoryNode

logger = logging.getLogger(__name__)

class MemoryDecayWorker:
    def __init__(self, check_interval_seconds: int = 3600):
        self.check_interval_seconds = check_interval_seconds
        self._task = None

    def start(self):
        if not self._task:
            self._task = asyncio.create_task(self._run_loop())
            logger.info("MemoryDecayWorker started.")

    def stop(self):
        if self._task:
            self._task.cancel()
            self._task = None
            logger.info("MemoryDecayWorker stopped.")

    async def _run_loop(self):
        while True:
            try:
                await self._decay_memories()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in MemoryDecayWorker: {e}")
            
            await asyncio.sleep(self.check_interval_seconds)

    async def _decay_memories(self):
        """Giảm weight của các memory node không được truy cập gần đây."""
        async with db_manager.session() as db:
            # Lấy các nodes chưa được truy cập trong 1 ngày qua
            one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
            
            stmt = select(MemoryNode).where(MemoryNode.last_accessed < one_day_ago)
            result = await db.execute(stmt)
            nodes = result.scalars().all()

            if not nodes:
                return

            decayed_count = 0
            deleted_count = 0
            
            for node in nodes:
                # Trừ trọng số đi 0.5 mỗi ngày không truy cập
                node.weight -= 0.5
                decayed_count += 1
                
                # Nếu trọng số rớt xuống dưới 0 và đã không dùng quá 30 ngày -> xóa
                thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
                if node.weight <= 0 and node.last_accessed < thirty_days_ago:
                    await db.delete(node)
                    deleted_count += 1
                    decayed_count -= 1
            
            await db.commit()
            logger.info(f"MemoryDecayWorker: Decayed {decayed_count} nodes, deleted {deleted_count} stale nodes.")
