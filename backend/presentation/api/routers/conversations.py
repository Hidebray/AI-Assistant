from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import List, Dict, Any

from backend.infrastructure.database.session import get_db_session
from backend.infrastructure.database.models import User, Conversation, Message
from backend.presentation.api.dependencies import get_current_user

router = APIRouter(prefix="/api/conversations", tags=["conversations"])

@router.get("")
async def get_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Lấy danh sách các đoạn hội thoại của user kèm số lượng tin nhắn."""
    stmt = (
        select(Conversation, func.count(Message.id).label('message_count'))
        .outerjoin(Message, Conversation.id == Message.conversation_id)
        .where(Conversation.user_id == current_user.id)
        .where(Conversation.status == "active")
        .group_by(Conversation.id)
        .order_by(desc(Conversation.updated_at))
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    return [
        {
            "id": row.Conversation.id,
            "title": row.Conversation.title or "New Conversation",
            "updated_at": row.Conversation.updated_at.isoformat(),
            "message_count": row.message_count
        }
        for row in rows
    ]


from pydantic import BaseModel
from typing import Optional

class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"

@router.post("")
async def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Tạo một đoạn hội thoại mới."""
    new_conv = Conversation(
        user_id=current_user.id,
        title=data.title or "New Conversation",
        status="active"
    )
    db.add(new_conv)
    await db.commit()
    await db.refresh(new_conv)
    
    return {
        "id": new_conv.id,
        "title": new_conv.title,
        "updated_at": new_conv.updated_at.isoformat()
    }

@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Xóa (soft delete) một đoạn hội thoại."""
    stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    )
    result = await db.execute(stmt)
    conv = result.scalar_one_or_none()
    
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    await db.delete(conv)
    await db.commit()
    return {"status": "success"}


@router.get("/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Lấy lịch sử tin nhắn của một đoạn hội thoại."""
    # Xác minh quyền sở hữu
    stmt_conv = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    )
    result_conv = await db.execute(stmt_conv)
    if not result_conv.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Conversation not found")

    stmt_msgs = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    result_msgs = await db.execute(stmt_msgs)
    messages = result_msgs.scalars().all()
    
    return [
        {
            "id": m.id,
            "sender_role": m.sender_role,
            "content": m.content,
            "metadata": m.metadata_,
            "plan": m.metadata_.get("plan") if m.metadata_ else None,
            "created_at": m.created_at.isoformat()
        }
        for m in messages
    ]
