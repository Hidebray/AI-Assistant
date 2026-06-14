from enum import Enum
from pydantic import BaseModel
from typing import Optional

class Urgency(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"

class RuleResult(BaseModel):
    is_matched: bool
    urgency: Optional[Urgency] = None
    message: Optional[str] = None
    weight: int = 0
    action_payload: Optional[dict] = None
