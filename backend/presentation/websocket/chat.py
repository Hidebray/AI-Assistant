import json
import logging
import os
from typing import Dict
from dotenv import load_dotenv
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from datetime import datetime, timezone

from backend.infrastructure.database.session import db_manager
from backend.application.security import decode_access_token
from backend.application.use_cases.llm_factory import LLMFactory
from backend.infrastructure.database.models import User, Session, Message, Conversation, MemoryNode
import asyncio

load_dotenv()
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.authenticated_users: Dict[str, User] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.authenticated_users:
            del self.authenticated_users[client_id]

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

manager = ConnectionManager()

async def authenticate_ws(token: str) -> User | None:
    """Tự tạo DB session riêng để tránh lỗi greenlet."""
    async with db_manager.session() as db:
        # --- DEV BYPASS (controlled by DEV_MODE env var) ---
        if DEV_MODE and (not token or token == "dummy_token"):
            stmt = select(User).where(User.username == "master_admin")
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                return user
        # ------------------

        payload = decode_access_token(token)
        if not payload or "sub" not in payload:
            return None
            
        username = payload["sub"]
        stmt = select(Session).where(Session.token == token)
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if session is None or session.is_revoked or session.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
            return None

        stmt_user = select(User).where(User.username == username)
        result_user = await db.execute(stmt_user)
        return result_user.scalar_one_or_none()

@router.websocket("/chat/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    client_id: str,
):
    await manager.connect(websocket, client_id)
    user: User | None = None
    
    try:
        # 1. Handshake authentication
        data = await websocket.receive_text()
        try:
            payload = json.loads(data)
            if payload.get("type") != "AUTHENTICATE" or not payload.get("token"):
                await websocket.close(code=1008, reason="Policy Violation: Authentication required")
                manager.disconnect(client_id)
                return
                
            user = await authenticate_ws(payload.get("token"))
            if not user:
                await websocket.close(code=1008, reason="Policy Violation: Invalid token")
                manager.disconnect(client_id)
                return
                
            manager.authenticated_users[client_id] = user
            await websocket.send_json({"type": "AUTHENTICATED", "message": "Ready"})
            
        except json.JSONDecodeError:
            await websocket.close(code=1008, reason="Policy Violation: Invalid format")
            manager.disconnect(client_id)
            return

        # 2. Main loop with Worker Separation
        out_queue = asyncio.Queue()
        event_bus = websocket.app.state.event_bus

        async def on_stream_chunk(event):
            if event.client_id == client_id:
                await out_queue.put({"type": "chunk", "content": event.chunk})

        async def on_status(event):
            if event.client_id == client_id:
                await out_queue.put({"type": "status", "content": event.status})

        async def on_plan(event):
            if event.client_id == client_id:
                await out_queue.put({"type": "plan", "content": event.plan_data})

        async def on_done(event):
            if event.client_id == client_id:
                if getattr(event, "error", None):
                    await out_queue.put({"type": "error", "content": event.error})
                else:
                    await out_queue.put({"type": "done"})

        async def on_alert_triggered(event):
            await out_queue.put({
                "type": "alert",
                "urgency": getattr(event, "urgency_level", "low"),
                "message": getattr(event, "alert_message", "")
            })

        async def on_system_notification(event):
            message = getattr(event, "message", getattr(event, "subject", "Thông báo mới"))
            if hasattr(event, "event_title"):
                title = "Đồng bộ tự động"
            elif hasattr(event, "subject"):
                title = getattr(event, "sender", "Email mới")
            else:
                title = getattr(event, "title", "Sự kiện")
                
            await out_queue.put({
                "type": "notification",
                "title": title,
                "message": message,
                "is_important": False
            })

        async def on_network_changed(event):
            await out_queue.put({
                "type": "network_state",
                "is_online": getattr(event, "is_online", True)
            })

        event_bus.subscribe("Chat.StreamChunk", on_stream_chunk)
        event_bus.subscribe("Chat.Status", on_status)
        event_bus.subscribe("Chat.Plan", on_plan)
        event_bus.subscribe("Chat.Done", on_done)
        event_bus.subscribe("Agent.AlertTriggered", on_alert_triggered)
        event_bus.subscribe("System.NewEmail", on_system_notification)
        event_bus.subscribe("System.NewCalendarEvent", on_system_notification)
        event_bus.subscribe("System.AutonomousSync", on_system_notification)
        event_bus.subscribe("NetworkMonitor", on_network_changed)

        async def ws_receiver():
            try:
                while True:
                    data = await websocket.receive_text()
                    try:
                        msg_payload = json.loads(data)
                        msg_type = msg_payload.get("type")
                        
                        if msg_type == "chat_message":
                            content = msg_payload.get("content", "")
                            conversation_id = msg_payload.get("conversation_id")
                            
                            async with db_manager.session() as db:
                                if not conversation_id:
                                    conversation = Conversation(user_id=user.id, title="Cuộc trò chuyện")
                                    db.add(conversation)
                                    await db.commit()
                                    await db.refresh(conversation)
                                    conversation_id = conversation.id
                                else:
                                    # Verification
                                    stmt_conv = select(Conversation).where(
                                        Conversation.id == conversation_id,
                                        Conversation.user_id == user.id
                                    )
                                    res_conv = await db.execute(stmt_conv)
                                    conversation = res_conv.scalar_one_or_none()
                                    if not conversation:
                                        conversation = Conversation(user_id=user.id, title="Cuộc trò chuyện")
                                        db.add(conversation)
                                        await db.commit()
                                        await db.refresh(conversation)
                                        conversation_id = conversation.id
                                
                                user_msg = Message(
                                    conversation_id=conversation_id,
                                    sender_role="user",
                                    source_origin="chat_ui",
                                    content=content
                                )
                                db.add(user_msg)
                                await db.commit()

                            from backend.domain.events.chat_events import ChatRequestedEvent
                            await event_bus.publish(ChatRequestedEvent(
                                source_origin="websocket",
                                conversation_id=conversation_id,
                                user_id=user.id,
                                client_id=client_id,
                                content=content,
                                language=msg_payload.get("language", "vi")
                            ))
                            
                        elif msg_type == "NETWORK_UPDATE":
                            is_online = msg_payload.get("is_online", True)
                            from backend.domain.events.chat_events import NetworkStateChangedEvent
                            await event_bus.publish(NetworkStateChangedEvent(
                                source_origin="websocket",
                                is_online=is_online
                            ))
                            
                        elif msg_type == "CANCEL_GENERATION":
                            from backend.domain.events.chat_events import ChatCancelRequestedEvent
                            await event_bus.publish(ChatCancelRequestedEvent(
                                source_origin="websocket",
                                client_id=client_id
                            ))
                            
                    except Exception as e:
                        logger.error(f"Error handling WS message: {e}", exc_info=True)
                        await out_queue.put({"type": "error", "content": "Đã xảy ra lỗi, vui lòng thử lại."})
            except WebSocketDisconnect:
                pass

        async def ws_sender():
            try:
                while True:
                    msg = await out_queue.get()
                    await websocket.send_json(msg)
            except WebSocketDisconnect:
                pass

        # Run concurrent loops
        receive_task = asyncio.create_task(ws_receiver())
        send_task = asyncio.create_task(ws_sender())
        
        done, pending = await asyncio.wait(
            [receive_task, send_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()

    except WebSocketDisconnect:
        pass
    finally:
        if 'event_bus' in locals() and 'on_stream_chunk' in locals():
            event_bus.unsubscribe("Chat.StreamChunk", on_stream_chunk)
            event_bus.unsubscribe("Chat.Status", on_status)
            event_bus.unsubscribe("Chat.Plan", on_plan)
            event_bus.unsubscribe("Chat.Done", on_done)
            event_bus.unsubscribe("Agent.AlertTriggered", on_alert_triggered)
            event_bus.unsubscribe("System.NewEmail", on_system_notification)
            event_bus.unsubscribe("System.NewCalendarEvent", on_system_notification)
            event_bus.unsubscribe("System.AutonomousSync", on_system_notification)
            event_bus.unsubscribe("NetworkMonitor", on_network_changed)
        manager.disconnect(client_id)
