import asyncio
from backend.infrastructure.database.session import db_manager
from sqlalchemy import select
from backend.infrastructure.database.models import UserSetting

async def main():
    async with db_manager.session() as db:
        res = await db.execute(select(UserSetting))
        settings = res.scalars().all()
        print([{s.setting_key: s.setting_value} for s in settings])

asyncio.run(main())
