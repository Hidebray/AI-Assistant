from backend.domain.interfaces.alert_rule import IAlertRule
from backend.domain.events.base_events import BaseEvent, AutonomousSyncEvent
from backend.application.dtos.alert_dtos import RuleResult, Urgency

class AutoSyncRule(IAlertRule):
    @property
    def weight(self) -> int:
        return 100

    def evaluate(self, event: BaseEvent) -> RuleResult:
        if isinstance(event, AutonomousSyncEvent):
            message = event.message or f"Đã tự động thêm sự kiện '{event.event_title}' vào lịch."
            return RuleResult(
                is_matched=True,
                urgency=Urgency.INFO,
                message=message
            )
        return RuleResult(is_matched=False)
