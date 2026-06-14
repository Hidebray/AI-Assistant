from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from enum import Enum

class UserInputDTO(BaseModel):
    conversation_id: str
    text: str
    metadata: Optional[Dict[str, Any]] = None

class AgentResponseDTO(BaseModel):
    conversation_id: str
    response_text: str
    action_taken: str

class ContextDTO(BaseModel):
    history: List[str]
    recent_input: str

class ActionType(str, Enum):
    TOOL_CALL = "TOOL_CALL"
    DONE = "DONE"

class ActionDTO(BaseModel):
    action_type: ActionType = Field(..., description="'TOOL_CALL' if a tool is needed, 'DONE' if you have enough info to answer the user directly.")
    tool_name: Optional[str] = Field(None, description="Name of the tool to call if action_type is TOOL_CALL")
    tool_arguments: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Arguments to pass to the tool if action_type is TOOL_CALL")

class ToolResultDTO(BaseModel):
    tool_name: str
    is_success: bool
    result_data: Any
    error_message: Optional[str] = None
