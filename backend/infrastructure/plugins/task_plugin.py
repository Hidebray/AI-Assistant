import logging
from datetime import datetime, timezone
import dateutil.parser
from backend.infrastructure.plugins.base import BasePlugin
from backend.domain.interfaces.event_bus import IEventBus
from backend.infrastructure.database.session import db_manager
from backend.infrastructure.database.models import Task, User
from sqlalchemy import select, update

logger = logging.getLogger(__name__)

class TaskPlugin(BasePlugin):
    def __init__(self):
        self.bus = None
        self.is_running = False

    async def on_stop(self):
        self.is_running = False
        logger.info("[TaskPlugin] Stopped.")

    def get_metadata(self) -> dict:
        return {
            "name": "task_plugin",
            "version": "1.0",
            "permissions": ["db_write"],
            "tools": [
                {
                    "name": "create_task",
                    "description": "Create a new task or todo item.",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string", "description": "The ID of the user."},
                            "title": {"type": "string", "description": "Title of the task"},
                            "description": {"type": "string", "description": "Description of the task (optional)"},
                            "deadline": {"type": "string", "format": "date-time", "description": "Deadline of the task. MUST BE LOCAL TIME. DO NOT append 'Z'."},
                            "priority": {"type": "string", "enum": ["low", "medium", "high"], "description": "Priority of the task (default: medium)"}
                        },
                        "required": ["user_id", "title"]
                    }
                },
                {
                    "name": "get_tasks",
                    "description": "Retrieve the list of tasks for the user.",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string", "description": "The ID of the user."},
                            "status": {"type": "string", "enum": ["pending", "in_progress", "completed", "all"], "description": "Filter by status (default: pending)"}
                        },
                        "required": ["user_id"]
                    }
                },
                {
                    "name": "update_task_status",
                    "description": "Update the status of a task (e.g., mark as completed).",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string", "description": "The ID of the user."},
                            "title_keyword": {"type": "string", "description": "Keyword from the title of the task to update."},
                            "new_status": {"type": "string", "enum": ["pending", "in_progress", "completed"], "description": "The new status of the task."}
                        },
                        "required": ["user_id", "title_keyword", "new_status"]
                    }
                },
                {
                    "name": "delete_task",
                    "description": "Delete a specific task based on a title keyword.",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string", "description": "The ID of the user."},
                            "title_keyword": {"type": "string", "description": "Keyword from the title of the task to delete."}
                        },
                        "required": ["user_id", "title_keyword"]
                    }
                }
            ]
        }

    async def on_load(self):
        logger.info("[TaskPlugin] Loaded configuration.")

    async def on_start(self, event_bus: IEventBus):
        self.bus = event_bus
        self.is_running = True
        logger.info("[TaskPlugin] Started.")

    async def execute_tool(self, tool_name: str, payload: dict):
        if tool_name == "create_task":
            return await self._create_task(payload)
        elif tool_name == "get_tasks":
            return await self._get_tasks(payload)
        elif tool_name == "update_task_status":
            return await self._update_task_status(payload)
        elif tool_name == "delete_task":
            return await self._delete_task(payload)
        else:
            return {"status": "error", "message": f"Unknown tool: {tool_name}"}

    async def _create_task(self, payload: dict):
        language = payload.get("language", "vi")
        user_id = payload.get("user_id")
        title = payload.get("title")
        description = payload.get("description")
        deadline_str = payload.get("deadline")
        priority = payload.get("priority", "medium")

        if not user_id or not title:
            return {"status": "error", "message": "Thiếu user_id hoặc title" if language == "vi" else "Missing required fields: user_id, title"}

        deadline_utc = None
        if deadline_str:
            try:
                local_tz = datetime.now().astimezone().tzinfo
                dt = dateutil.parser.parse(deadline_str)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=local_tz)
                deadline_utc = dt.astimezone(timezone.utc).replace(tzinfo=None)
            except Exception as e:
                return {"status": "error", "message": f"Định dạng thời gian không hợp lệ: {e}" if language == "vi" else f"Invalid deadline format: {e}"}

        async with db_manager.session() as db:
            user = await db.get(User, user_id)
            if not user:
                return {"status": "error", "message": "Không tìm thấy người dùng" if language == "vi" else "User not found"}

            new_task = Task(
                user_id=user_id,
                title=title,
                description=description,
                deadline=deadline_utc,
                priority=priority,
                status="pending",
                source_origin="agent"
            )
            db.add(new_task)
            await db.commit()

        return {
            "status": "success",
            "message": f"Đã tạo công việc '{title}' thành công." if language == "vi" else f"Task '{title}' created successfully.",
            "data": {
                "title": title,
                "deadline": deadline_str,
                "priority": priority
            }
        }

    async def _get_tasks(self, payload: dict):
        language = payload.get("language", "vi")
        user_id = payload.get("user_id")
        status_filter = payload.get("status", "pending")

        if not user_id:
            return {"status": "error", "message": "Thiếu user_id" if language == "vi" else "Missing user_id"}

        async with db_manager.session() as db:
            stmt = select(Task).where(Task.user_id == user_id, Task.is_deleted == False)
            if status_filter != "all":
                stmt = stmt.where(Task.status == status_filter)
            
            stmt = stmt.order_by(Task.deadline.asc().nulls_last())
            
            result = await db.execute(stmt)
            tasks = result.scalars().all()

            if not tasks:
                return {"status": "success", "message": f"Không tìm thấy công việc nào trạng thái {status_filter}." if language == "vi" else f"No {status_filter} tasks found.", "tasks": []}

            local_tz = datetime.now().astimezone().tzinfo
            task_list = []
            for t in tasks:
                deadline_local_str = None
                if t.deadline:
                    dt_utc = t.deadline.replace(tzinfo=timezone.utc)
                    dt_local = dt_utc.astimezone(local_tz)
                    deadline_local_str = dt_local.strftime("%Y-%m-%d %H:%M:%S")
                
                task_list.append({
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "status": t.status,
                    "priority": t.priority,
                    "deadline": deadline_local_str
                })

        return {
            "status": "success",
            "message": f"Tìm thấy {len(task_list)} công việc." if language == "vi" else f"Found {len(task_list)} tasks.",
            "tasks": task_list
        }

    async def _update_task_status(self, payload: dict):
        language = payload.get("language", "vi")
        user_id = payload.get("user_id")
        title_keyword = payload.get("title_keyword")
        new_status = payload.get("new_status")

        if not user_id or not title_keyword or not new_status:
            return {"status": "error", "message": "Thiếu thông tin bắt buộc" if language == "vi" else "Missing user_id, title_keyword, or new_status"}

        async with db_manager.session() as db:
            stmt = select(Task).where(
                Task.user_id == user_id,
                Task.is_deleted == False,
                Task.title.ilike(f"%{title_keyword}%")
            ).order_by(Task.created_at.desc()).limit(1)
            
            result = await db.execute(stmt)
            task = result.scalar_one_or_none()

            if not task:
                return {"status": "error", "message": f"Không tìm thấy công việc nào chứa từ khóa '{title_keyword}'" if language == "vi" else f"No task found matching '{title_keyword}'"}

            task.status = new_status
            await db.commit()

        return {"status": "success", "message": f"Đã đánh dấu công việc '{task.title}' là {new_status}." if language == "vi" else f"Task '{task.title}' marked as {new_status}."}

    async def _delete_task(self, payload: dict):
        language = payload.get("language", "vi")
        user_id = payload.get("user_id")
        title_keyword = payload.get("title_keyword")

        if not user_id or not title_keyword:
            return {"status": "error", "message": "Thiếu thông tin bắt buộc" if language == "vi" else "Missing user_id or title_keyword"}

        async with db_manager.session() as db:
            stmt = select(Task).where(
                Task.user_id == user_id,
                Task.is_deleted == False,
                Task.title.ilike(f"%{title_keyword}%")
            ).order_by(Task.created_at.desc()).limit(1)
            
            result = await db.execute(stmt)
            task = result.scalar_one_or_none()

            if not task:
                return {"status": "error", "message": f"Không tìm thấy công việc nào chứa từ khóa '{title_keyword}'" if language == "vi" else f"No task found matching '{title_keyword}'"}

            task.is_deleted = True
            await db.commit()

        return {"status": "success", "message": f"Đã xóa công việc '{task.title}'." if language == "vi" else f"Task '{task.title}' deleted."}
