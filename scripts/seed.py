import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.application.security import get_password_hash
from backend.infrastructure.database.models import Conversation, Message, Session, User
from backend.infrastructure.database.session import DATABASE_URL

DEV_ADMIN_PASSWORD = os.getenv("DEV_ADMIN_PASSWORD", "password")


async def seed_data():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(select(User).where(User.username == "master_admin"))
        master_user = result.scalar_one_or_none()

        if master_user is None:
            master_user = User(
                username="master_admin",
                password_hash=get_password_hash(DEV_ADMIN_PASSWORD),
                is_active=True,
            )
            session.add(master_user)
            await session.flush()
        else:
            master_user.password_hash = get_password_hash(DEV_ADMIN_PASSWORD)
            master_user.is_active = True

        result = await session.execute(
            select(Conversation).where(Conversation.user_id == master_user.id)
        )
        conversation = result.scalars().first()
        if conversation is None:
            conversation = Conversation(
                user_id=master_user.id,
                title="Cuộc trò chuyện khởi tạo",
                status="active",
            )
            session.add(conversation)
            await session.flush()

            session.add(
                Message(
                    conversation_id=conversation.id,
                    sender_role="system",
                    content="Xin chào! Tôi là Autonomous AI Assistant của bạn. Tôi có thể giúp gì cho bạn hôm nay?",
                )
            )

        result = await session.execute(
            select(Session).where(Session.token == "dummy_jwt_token_for_development")
        )
        app_session = result.scalar_one_or_none()
        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=7)
        if app_session is None:
            session.add(
                Session(
                    user_id=master_user.id,
                    token="dummy_jwt_token_for_development",
                    expires_at=expires_at,
                )
            )
        else:
            app_session.user_id = master_user.id
            app_session.expires_at = expires_at
            app_session.is_revoked = False

        await session.commit()

    await engine.dispose()
    print("Data seeded successfully.")


if __name__ == "__main__":
    asyncio.run(seed_data())
