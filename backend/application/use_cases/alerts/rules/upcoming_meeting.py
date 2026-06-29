from datetime import datetime, timezone
from backend.domain.interfaces.alert_rule import IAlertRule
from backend.application.dtos.alert_dtos import RuleResult, Urgency
from backend.domain.events.base_events import SystemNewCalendarEvent

class UpcomingMeetingRule(IAlertRule):
    def evaluate(self, event_data: any) -> RuleResult:
        if not isinstance(event_data, SystemNewCalendarEvent):
            return RuleResult(is_matched=False)
            
        start_time_iso = event_data.start_time
        if not start_time_iso: 
            return RuleResult(is_matched=False)
        
        try:
            start_time = datetime.fromisoformat(start_time_iso.replace("Z", "+00:00"))
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            current_utc = datetime.now(timezone.utc)
            time_diff = start_time - current_utc
            
            # Khớp nếu diễn ra trong vòng 5 phút tới hoặc đã bắt đầu không quá 15 phút
            if -15 * 60 <= time_diff.total_seconds() <= 5 * 60:
                title = event_data.title
                return RuleResult(
                    is_matched=True, 
                    urgency=Urgency.HIGH, 
                    weight=80,
                    message=f"Sắp tới giờ sự kiện: {title}"
                )
        except Exception:
            pass
            
        return RuleResult(is_matched=False)
