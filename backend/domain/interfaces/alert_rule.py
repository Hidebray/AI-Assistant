from abc import ABC, abstractmethod
from typing import Any
from backend.application.dtos.alert_dtos import RuleResult

class IAlertRule(ABC):
    """
    Interface bắt buộc cho mọi tập luật cảnh báo (Alert Rule).
    Tuân thủ OCP: Mỗi Rule mới là một class kế thừa interface này.
    """

    @abstractmethod
    def evaluate(self, event_data: Any) -> RuleResult:
        """
        Đánh giá sự kiện và trả về RuleResult.
        """
        pass
