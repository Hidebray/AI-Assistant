import asyncio
import sys
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.infrastructure.database.models import Base
from backend.infrastructure.database.session import DATABASE_URL

async def main():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('Schema updated!')

if __name__ == '__main__':
    asyncio.run(main())
