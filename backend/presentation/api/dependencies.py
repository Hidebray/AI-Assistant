import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import AsyncIterator
from dotenv import load_dotenv

from backend.infrastructure.database.session import db_manager, get_db_session
from backend.infrastructure.database.models import User, Session
from backend.application.security import decode_access_token
from backend.infrastructure.messaging.async_event_bus import LocalEventBus
from datetime import datetime, timezone

load_dotenv()
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

# We will attach the event bus to the FastAPI app state in main.py
from fastapi import Request

def get_event_bus(request: Request) -> LocalEventBus:
    return request.app.state.event_bus

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db_session)
) -> User:
    # --- DEV BYPASS (controlled by DEV_MODE env var) ---
    if DEV_MODE and not token:
        stmt = select(User).where(User.username == "master_admin")
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            return user
    # ------------------

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
        
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    # Check session in DB to see if it's revoked or expired
    stmt = select(Session).where(Session.token == token)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    
    if session is None or session.is_revoked or session.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        raise credentials_exception

    # Get user
    stmt_user = select(User).where(User.username == username)
    result_user = await db.execute(stmt_user)
    user = result_user.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
        
    return user
