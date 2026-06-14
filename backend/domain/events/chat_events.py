from pydantic import Field
from typing import Dict, Any, Optional
from backend.domain.events.base_events import BaseEvent

class ChatRequestedEvent(BaseEvent):
    event_type: str = "Chat.Requested"
    conversation_id: str
    user_id: str
    client_id: str
    content: str
    language: str = "vi"

class ChatStreamChunkEvent(BaseEvent):
    event_type: str = "Chat.StreamChunk"
    client_id: str
    chunk: str

class ChatStatusEvent(BaseEvent):
    event_type: str = "Chat.Status"
    client_id: str
    status: str

class ChatDoneEvent(BaseEvent):
    event_type: str = "Chat.Done"
    client_id: str
    error: Optional[str] = None

class NetworkStateChangedEvent(BaseEvent):
    event_type: str = "Network.StateChanged"
    is_online: bool

class ChatCancelRequestedEvent(BaseEvent):
    event_type: str = "Chat.CancelRequested"
    client_id: str
