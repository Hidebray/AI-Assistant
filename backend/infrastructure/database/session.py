import contextlib
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import event

import os
import sys

def get_database_url() -> str:
    if getattr(sys, 'frozen', False):
        # Production Mode (PyInstaller bundle)
        appdata_dir = os.getenv('APPDATA', os.path.expanduser("~"))
        db_dir = os.path.join(appdata_dir, "com.aaa.app", "database")
    else:
        # Development Mode (Since session.py is in backend/infrastructure/database,
        # we go up 2 levels to backend/, then into database/)
        db_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "database"))
    
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "app_data.db").replace('\\', '/')
    return f"sqlite+aiosqlite:///{db_path}"

# We use standard aiosqlite for this iteration as approved
DATABASE_URL = get_database_url()
class DatabaseSessionManager:
    def __init__(self, host: str):
        self._engine: AsyncEngine | None = create_async_engine(host, echo=False)
        self._sessionmaker: async_sessionmaker[AsyncSession] | None = async_sessionmaker(
            autocommit=False, autoflush=False, bind=self._engine
        )

        # Apply PRAGMA journal_mode=WAL when connecting
        @event.listens_for(self._engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()

    async def close(self):
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        await self._engine.dispose()

        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncEngine]:
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise Exception("DatabaseSessionManager is not initialized")

        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

db_manager = DatabaseSessionManager(DATABASE_URL)

async def get_db_session() -> AsyncIterator[AsyncSession]:
    """FastAPI Dependency for getting db session"""
    async with db_manager.session() as session:
        yield session
