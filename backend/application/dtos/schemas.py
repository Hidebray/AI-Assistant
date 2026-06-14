from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field

class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class UserBase(BaseSchema):
    username: str
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

class SessionBase(BaseSchema):
    token: str
    expires_at: datetime
    is_revoked: bool = False

class SessionCreate(SessionBase):
    user_id: str

class SessionOut(SessionBase):
    id: str
    user_id: str
    created_at: datetime

class ConversationBase(BaseSchema):
    title: Optional[str] = None
    status: str = "active"

class ConversationCreate(ConversationBase):
    user_id: str

class ConversationOut(ConversationBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

class MessageBase(BaseSchema):
    sender_role: str
    source_origin: str = "user"
    content: str
    metadata_: Optional[dict[str, Any]] = Field(default=None, alias="metadata")

class MessageCreate(MessageBase):
    conversation_id: str

class MessageOut(MessageBase):
    id: str
    conversation_id: str
    created_at: datetime

class TaskBase(BaseSchema):
    source_origin: str
    title: str
    description: Optional[str] = None
    status: str = "pending"
    due_date: Optional[datetime] = None

class TaskCreate(TaskBase):
    user_id: str

class TaskOut(TaskBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

class CalendarEventBase(BaseSchema):
    source_id: Optional[str] = None
    source_origin: str
    title: str
    start_time: datetime
    end_time: datetime
    location: Optional[str] = None

class CalendarEventCreate(CalendarEventBase):
    user_id: str

class CalendarEventOut(CalendarEventBase):
    id: str
    user_id: str
    created_at: datetime

class MemoryNodeBase(BaseSchema):
    context_key: str
    source_origin: str
    content: str
    weight: float = 1.0

class MemoryNodeCreate(MemoryNodeBase):
    user_id: str

class MemoryNodeOut(MemoryNodeBase):
    id: str
    user_id: str
    created_at: datetime
    last_accessed: datetime
