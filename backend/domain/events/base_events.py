from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime, timezone
import uuid

def utc_now():
    return datetime.now(timezone.utc)

# ==========================================
# LỚP CƠ SỞ (BASE EVENT)
# ==========================================
class BaseEvent(BaseModel):
    """Định nghĩa cấu trúc chung cho mọi sự kiện trong Event Bus."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=utc_now)
    source_origin: str = Field(..., description="Định danh module phát ra sự kiện")
    event_type: str = Field(..., description="Tên loại sự kiện để Router phân loại")

# ==========================================
# NHÓM 1: SỰ KIỆN HỆ THỐNG (SYSTEM EVENTS)
# ==========================================
class SystemEvent(BaseEvent):
    """Sự kiện liên quan đến vòng đời ứng dụng và các tiến trình nền."""
    status: str = Field(..., description="success, failed, warning")
    message: str

class PluginLoadedEvent(SystemEvent):
    event_type: str = "System.PluginLoaded"
    plugin_name: str
    version: str

class CrawlerFinishedEvent(SystemEvent):
    event_type: str = "System.CrawlerFinished"
    total_records_processed: int
    new_items_found: int

class SystemNewEmailEvent(SystemEvent):
    event_type: str = "System.NewEmail"
    sender: str
    subject: str
    body: str

class SystemNewCalendarEvent(SystemEvent):
    event_type: str = "System.NewCalendarEvent"
    title: str
    start_time: str
    end_time: str
    location: Optional[str] = None

# ==========================================
# NHÓM 2: SỰ KIỆN TỪ NGƯỜI DÙNG (USER EVENTS)
# ==========================================
class UserEvent(BaseEvent):
    """Sự kiện sinh ra từ các thao tác trực tiếp của người dùng trên UI."""
    user_id: str

class UserMessageSentEvent(UserEvent):
    event_type: str = "User.MessageSent"
    conversation_id: str
    content: str

class SettingsChangedEvent(UserEvent):
    event_type: str = "User.SettingsChanged"
    setting_key: str
    new_value: Any

# ==========================================
# NHÓM 3: SỰ KIỆN TỪ AI LÕI (AGENT EVENTS)
# ==========================================
class AgentEvent(BaseEvent):
    """Sự kiện do AgentCore, Planner hoặc ToolExecutor phát ra."""
    correlation_id: str = Field(..., description="ID của yêu cầu gốc để trace luồng xử lý")

class AgentThinkingEvent(AgentEvent):
    event_type: str = "Agent.Thinking"
    current_action_description: str

class TaskCompletedEvent(AgentEvent):
    event_type: str = "Agent.TaskCompleted"
    task_id: str
    is_success: bool
    result_data: Optional[Dict[str, Any]] = None

class AlertTriggeredEvent(AgentEvent):
    event_type: str = "Agent.AlertTriggered"
    urgency_level: str = Field(..., pattern="^(low|medium|high|critical)$")
    alert_message: str

class ToolCallRequestEvent(AgentEvent):
    event_type: str = "Agent.ToolCallRequest"
    tool_name: str
    payload: Dict[str, Any] = Field(default_factory=dict)

class ToolResultEvent(AgentEvent):
    event_type: str = "Agent.ToolResult"
    tool_name: str
    is_success: bool
    result_data: Any

class AutonomousSyncEvent(SystemEvent):
    event_type: str = "System.AutonomousSync"
    event_title: str
    start_time: str
