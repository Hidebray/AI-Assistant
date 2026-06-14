from pydantic import BaseModel, Field
from typing import Optional

class EmailAnalysisDTO(BaseModel):
    has_event: bool = Field(description="True nếu email chứa thông tin về sự kiện, lịch hẹn, hoặc deadline.")
    is_urgent: bool = Field(description="True nếu email có tính chất khẩn cấp (URGENT/ASAP/QUAN TRỌNG/CẤP BÁCH).")
    event_title: Optional[str] = Field(None, description="Tên sự kiện hoặc tiêu đề cuộc họp/deadline (nếu có).")
    start_time: Optional[str] = Field(None, description="Thời gian bắt đầu theo định dạng ISO-8601 (nếu có).")
    end_time: Optional[str] = Field(None, description="Thời gian kết thúc theo định dạng ISO-8601 (nếu có).")
    summary: str = Field(description="Tóm tắt nội dung email trong 1 câu ngắn gọn.")
