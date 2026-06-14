from abc import ABC, abstractmethod
import re

class ICommand(ABC):
    pattern: str = ""
    help_text: str = ""

    @abstractmethod
    async def execute(self, match_dict: dict, user_id: str, language: str = "vi") -> str:
        """Thực thi lệnh và trả về kết quả dưới dạng chuỗi"""
        pass
