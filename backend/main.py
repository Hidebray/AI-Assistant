import os
import sys
import certifi

if getattr(sys, 'frozen', False):
    # Fix SSL certificates issue for httpx/openai in PyInstaller
    os.environ['SSL_CERT_FILE'] = certifi.where()
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from backend.presentation.api.limiter import limiter

from backend.presentation.api.routers import auth, settings, conversations, alerts, calendar, tasks, google_auth, ollama, notifications
from backend.presentation.websocket import chat
from backend.infrastructure.database.session import db_manager
from backend.infrastructure.messaging.async_event_bus import LocalEventBus
from backend.infrastructure.plugins.manager import PluginManager
from backend.infrastructure.plugins.calendar_plugin import CalendarPlugin
from backend.infrastructure.plugins.web_search_plugin import WebSearchPlugin
from backend.infrastructure.plugins.memory_plugin import MemoryPlugin
from backend.infrastructure.plugins.email_plugin import EmailPlugin
from backend.infrastructure.plugins.task_plugin import TaskPlugin
from backend.application.services.chat_worker import ChatWorker
from backend.application.use_cases.alerts.alert_engine import AlertEngine
from backend.application.use_cases.alerts.rules.upcoming_meeting import UpcomingMeetingRule
from backend.application.use_cases.alerts.rules.vip_email import VIPEmailRule
from backend.application.use_cases.alerts.rules.auto_sync_rule import AutoSyncRule
from backend.infrastructure.workers.memory_decay_worker import MemoryDecayWorker
from backend.infrastructure.workers.calendar_notifier import CalendarNotifierWorker
from backend.infrastructure.workers.email_scanner_worker import EmailScannerWorker
from backend.infrastructure.workers.task_notifier_worker import TaskNotifierWorker
from backend.infrastructure.workers.worker_manager import WorkerManager
from backend.application.services.auto_sync import AutoSyncEngine

# We need a repository mock for LocalEventBus for now
class MockRepository:
    async def save_dead_letter(self, *args, **kwargs):
        pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def _run_schema_migrations():
    """
    Safely run incremental column migrations for SQLite.
    Uses ALTER TABLE ADD COLUMN (no-op if column already exists).
    This handles cases where the production DB was created before new model columns were added.
    """
    from backend.infrastructure.database.session import db_manager
    migrations = [
        # (table_name, column_name, column_definition)
        ("calendar_events", "is_notified", "BOOLEAN DEFAULT 0"),
        ("tasks", "priority",    "VARCHAR(20) DEFAULT 'medium'"),
        ("tasks", "is_deleted",  "BOOLEAN DEFAULT 0"),
        ("tasks", "is_notified", "BOOLEAN DEFAULT 0"),
        ("tasks", "deadline",    "DATETIME"),
    ]
    async with db_manager._engine.connect() as conn:
        # Get existing columns for each table
        from sqlalchemy import text
        tables_checked: dict[str, set] = {}
        for table, column, col_def in migrations:
            if table not in tables_checked:
                result = await conn.execute(text(f"PRAGMA table_info({table})"))
                tables_checked[table] = {row[1] for row in result.fetchall()}
            
            if column not in tables_checked[table]:
                try:
                    await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}"))
                    await conn.commit()
                    logger.info(f"Schema migration: added column '{column}' to table '{table}'")
                except Exception as e:
                    logger.warning(f"Schema migration failed for {table}.{column}: {e}")

        # Data migration: clear old double-encrypted keys (Fernet tokens start with gAAAAAB...)
        try:
            await conn.execute(text("UPDATE user_settings SET setting_value = '' WHERE setting_key IN ('llm.gemini_key', 'llm.openai_key') AND setting_value LIKE 'gAAAAA%'"))
            await conn.execute(text("UPDATE user_settings SET setting_value = 'http://localhost:11434' WHERE setting_key = 'llm.ollama_url' AND setting_value LIKE 'gAAAAA%'"))
            await conn.commit()
            logger.info("Data migration: cleaned up old encrypted settings.")
        except Exception as e:
            logger.warning(f"Data migration failed: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up FastAPI application...")
    
    # Auto-create database tables
    from backend.infrastructure.database.models import Base
    from backend.infrastructure.database.session import db_manager
    async with db_manager._engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Run incremental schema migrations for columns added after initial deployment.
    # SQLite's CREATE TABLE IF NOT EXISTS won't add new columns to existing tables,
    # so we do safe ALTER TABLE ADD COLUMN calls for each missing field.
    await _run_schema_migrations()
    
    # Init Event Bus
    repo = MockRepository()
    event_bus = LocalEventBus(repository=repo)
    event_bus.start()
    app.state.event_bus = event_bus
    
    # Init Plugin Manager
    plugin_manager = PluginManager(event_bus=event_bus)
    await plugin_manager.register_plugin(CalendarPlugin())
    await plugin_manager.register_plugin(WebSearchPlugin())
    await plugin_manager.register_plugin(MemoryPlugin())
    await plugin_manager.register_plugin(EmailPlugin())
    await plugin_manager.register_plugin(TaskPlugin())
    await plugin_manager.discover_and_load()
    await plugin_manager.start_all()
    app.state.plugin_manager = plugin_manager
    
    # Init Chat Worker
    chat_worker = ChatWorker(event_bus=event_bus, plugin_manager=plugin_manager)
    chat_worker.start()
    app.state.chat_worker = chat_worker
    
    # Init Alert Engine
    alert_engine = AlertEngine(event_bus=event_bus)
    alert_engine.add_rule(UpcomingMeetingRule())
    alert_engine.add_rule(VIPEmailRule())
    alert_engine.add_rule(AutoSyncRule())
    app.state.alert_engine = alert_engine
    
    # Init Notification Service
    from backend.application.services.notification_service import NotificationService
    notification_service = NotificationService(event_bus=event_bus)
    notification_service.start()
    app.state.notification_service = notification_service
    
    # Subscribe Alert Engine to EventBus manually
    event_bus.subscribe("System.NewEmail", alert_engine.process_event)
    event_bus.subscribe("System.NewCalendarEvent", alert_engine.process_event)
    event_bus.subscribe("System.AutonomousSync", alert_engine.process_event)

    
    # Init WorkerManager (APScheduler)
    worker_manager = WorkerManager()
    
    # Register Memory Decay
    memory_decay_worker = MemoryDecayWorker()
    worker_manager.add_interval_job(memory_decay_worker._decay_memories, seconds=3600, job_id="memory_decay")
    
    # Register Calendar Notifier (runs every 60 seconds)
    calendar_notifier = CalendarNotifierWorker(app.state.event_bus)
    worker_manager.add_interval_job(calendar_notifier.check_upcoming_events, seconds=60, job_id="calendar_notifier")
    
    # Register Email Scanner (runs every 60 seconds)
    email_scanner = EmailScannerWorker(app.state.event_bus)
    worker_manager.add_interval_job(email_scanner.scan_unread_emails, seconds=60, job_id="email_scanner")
    
    # Register Task Notifier
    task_notifier = TaskNotifierWorker(app.state.event_bus)
    worker_manager.add_interval_job(task_notifier.check_pending_tasks, seconds=60, job_id="task_notifier")
    
    # Register Auto-Sync (runs every 15 mins = 900s)
    auto_sync_engine = AutoSyncEngine()
    worker_manager.add_interval_job(auto_sync_engine.sync_all_users, seconds=900, job_id="auto_sync")
    
    worker_manager.start()
    app.state.worker_manager = worker_manager
    
    # Auto-start Ollama server if installed
    from backend.infrastructure.llm.ollama_manager import ollama_manager
    try:
        start_result = await ollama_manager.start_server()
        if start_result["success"]:
            logger.info("Ollama server auto-started successfully")
        else:
            logger.info(f"Ollama auto-start skipped: {start_result['message']}")
    except Exception as e:
        logger.warning(f"Ollama auto-start failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    if hasattr(app.state, "worker_manager"):
        app.state.worker_manager.stop()
    if hasattr(app.state, "plugin_manager"):
        await app.state.plugin_manager.stop_all()
    await event_bus.stop()
    await db_manager.close()

app = FastAPI(
    title="Autonomous AI Assistant",
    description="Backend API for AAA",
    version="1.0.0",
    lifespan=lifespan
)

# Add Rate Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration
origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "tauri://localhost",
    "http://tauri.localhost",
    "https://tauri.localhost"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(settings.router)
app.include_router(calendar.router)
app.include_router(tasks.router)
app.include_router(conversations.router)
app.include_router(chat.router)
app.include_router(alerts.router)
app.include_router(google_auth.router)
app.include_router(ollama.router)
app.include_router(notifications.router)

@app.get("/")
async def root():
    return {"message": "Autonomous AI Assistant API is running"}

if __name__ == "__main__":
    import uvicorn
    import multiprocessing
    import sys
    
    # Bắt buộc cho PyInstaller trên Windows khi có sử dụng đa tiến trình (multiprocessing)
    multiprocessing.freeze_support()
    
    # Hỗ trợ lấy port từ tham số dòng lệnh (Tauri sidecar có thể truyền port vào)
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
            
    logger.info(f"Starting Backend Server on port {port}...")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
