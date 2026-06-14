import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from typing import Callable

logger = logging.getLogger(__name__)

class WorkerManager:
    """
    Central manager for all background cron jobs and scheduled tasks using APScheduler.
    """
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False

    def start(self):
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("WorkerManager (APScheduler) started.")

    def stop(self):
        if self.is_running:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("WorkerManager (APScheduler) stopped.")

    def add_interval_job(self, job_func: Callable, seconds: int, job_id: str, **kwargs):
        """Adds a recurring task running every X seconds."""
        self.scheduler.add_job(
            job_func,
            trigger=IntervalTrigger(seconds=seconds),
            id=job_id,
            replace_existing=True,
            kwargs=kwargs
        )
        logger.info(f"Registered interval job: {job_id} (every {seconds}s)")
