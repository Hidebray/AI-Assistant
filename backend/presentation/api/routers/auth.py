from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone

from backend.presentation.api.dependencies import get_db_session, get_current_user
from backend.presentation.api.limiter import limiter
from backend.application.dtos.auth_dtos import RegisterRequest, LoginRequest, TokenResponse, ChangePasswordRequest
from backend.infrastructure.database.models import User, Session
from backend.application.security import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db_session)):
    # Check if user already exists
    result = await db.execute(select(User))
    existing_users = result.scalars().all()
    if len(existing_users) > 0:
        # For this local assistant, we only allow 1 master user
        raise HTTPException(status_code=400, detail="A master user already exists. Registration locked.")

    # Create user
    hashed_password = get_password_hash(request.password)
    new_user = User(username=request.username, password_hash=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Generate token
    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(data={"sub": new_user.username}, expires_delta=expires_delta)
    
    # Save session
    expires_at = datetime.now(timezone.utc) + expires_delta
    new_session = Session(user_id=new_user.id, token=token, expires_at=expires_at.replace(tzinfo=None))
    db.add(new_session)
    await db.commit()

    return TokenResponse(access_token=token, token_type="bearer", expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60)

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/3minute")
async def login(request: Request, payload: LoginRequest, db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(User).where(User.username == payload.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(data={"sub": user.username}, expires_delta=expires_delta)
    
    expires_at = datetime.now(timezone.utc) + expires_delta
    new_session = Session(user_id=user.id, token=token, expires_at=expires_at.replace(tzinfo=None))
    db.add(new_session)
    await db.commit()

    return TokenResponse(access_token=token, token_type="bearer", expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60)

from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db_session)):
    stmt = select(Session).where(Session.token == token)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if session:
        session.is_revoked = True
        await db.commit()
    return {"status": "success", "message": "Logged out"}

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username}

@router.delete("/reset")
async def factory_reset(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    from backend.infrastructure.database.models import (
        Session, Conversation, Message, CalendarEvent, MemoryNode, UserSetting, Task, Notification
    )
    from sqlalchemy import delete
    
    # Delete child messages first (via subquery)
    await db.execute(delete(Message).where(Message.conversation_id.in_(
        select(Conversation.id).where(Conversation.user_id == current_user.id)
    )))
    # Delete everything else
    await db.execute(delete(Conversation).where(Conversation.user_id == current_user.id))
    await db.execute(delete(Session).where(Session.user_id == current_user.id))
    await db.execute(delete(CalendarEvent).where(CalendarEvent.user_id == current_user.id))
    await db.execute(delete(MemoryNode).where(MemoryNode.user_id == current_user.id))
    await db.execute(delete(UserSetting).where(UserSetting.user_id == current_user.id))
    await db.execute(delete(Task).where(Task.user_id == current_user.id))
    await db.execute(delete(Notification).where(Notification.user_id == current_user.id))
    
    # Finally delete the user
    await db.execute(delete(User).where(User.id == current_user.id))
    await db.commit()
    return {"status": "success", "message": "Factory reset complete"}

@router.put("/change-password")
async def change_password(request: ChangePasswordRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    if not verify_password(request.old_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect old password")
        
    current_user.password_hash = get_password_hash(request.new_password)
    db.add(current_user)
    await db.commit()
    
    return {"status": "success", "message": "Password changed successfully"}
