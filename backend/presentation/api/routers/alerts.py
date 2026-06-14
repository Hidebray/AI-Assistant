from fastapi import APIRouter, Request
from typing import Dict, Any

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.post("/trigger")
async def trigger_alert(request: Request, event_data: Dict[str, Any]):
    """
    Mock webhook endpoint to trigger events into the Alert Engine.
    Example payload for email:
    { "event_type": "System.NewEmail", "sender": "ceo@company.com", "subject": "URGENT", "body": "test" }
    """
    if hasattr(request.app.state, "alert_engine"):
        event = event_data
        event_type = event_data.get("event_type")
        if event_type == "System.NewEmail":
            from backend.domain.events.base_events import SystemNewEmailEvent
            event = SystemNewEmailEvent(
                source_origin=event_data.get("source_origin", "webhook"),
                status=event_data.get("status", "success"),
                message=event_data.get("message", "New unread email found"),
                sender=event_data.get("sender", "unknown@example.com"),
                subject=event_data.get("subject", "No Subject"),
                body=event_data.get("body", "")
            )
        await request.app.state.alert_engine.process_event(event)
        return {"status": "processed"}
    return {"status": "error", "message": "Alert engine not initialized"}
