import re
from datetime import datetime, timezone
from sqlalchemy import select, update
from backend.domain.interfaces.command import ICommand
from backend.infrastructure.database.session import db_manager
from backend.infrastructure.database.models import Task

class TaskCommand(ICommand):
    pattern = r"^/task\s*(?P<args>.*)?$"

    def get_help_text(self, lang: str) -> str:
        if lang == "en":
            return "**How to use /task:**\n- `/task` : View pending tasks.\n- `/task --all` : View all tasks.\n- `/task --add [Content]` : Add a new task.\n- `/task --done [Keyword]` : Mark a task as completed.\n- `/task --delete [Keyword]` : Delete a task."
        return "**Cách dùng lệnh /task:**\n- `/task` : Xem danh sách việc cần làm.\n- `/task --all` : Xem tất cả công việc.\n- `/task --add [Nội dung]` : Thêm việc mới.\n- `/task --done [Từ khóa]` : Đánh dấu xong việc.\n- `/task --delete [Từ khóa]` : Xóa công việc."

    @property
    def help_text(self) -> str:
        return self.get_help_text("vi")

    async def execute(self, match_dict: dict, user_id: str, language: str = "vi") -> str:
        args_str = match_dict.get('args', '').strip()
        
        if args_str == "--help":
            return self.get_help_text(language)
            
        if args_str.startswith("-") and not args_str.startswith("--"):
            return "Invalid command. Use double dashes (--help, --add, --done, --delete, --all)." if language == "en" else "Lệnh không hợp lệ. Chỉ chấp nhận các cờ có 2 dấu trừ (VD: --help, --add, --done, --delete, --all)."

        local_tz = datetime.now().astimezone().tzinfo

        async with db_manager.session() as db:
            if args_str.startswith("--add "):
                title = args_str.replace("--add ", "", 1).strip()
                if not title:
                    return "Please provide a task title." if language == "en" else "Vui lòng nhập nội dung công việc."
                
                new_task = Task(
                    user_id=user_id,
                    title=title,
                    status="pending",
                    source_origin="offline_task"
                )
                db.add(new_task)
                await db.commit()
                return f"Added task: '{title}'" if language == "en" else f"Đã thêm công việc: '{title}'"

            elif args_str.startswith("--done "):
                keyword = args_str.replace("--done ", "", 1).strip()
                if not keyword:
                    return "Please provide a keyword." if language == "en" else "Vui lòng nhập từ khóa công việc."
                
                stmt = select(Task).where(
                    Task.user_id == user_id,
                    Task.is_deleted == False,
                    Task.status != "completed",
                    Task.title.ilike(f"%{keyword}%")
                ).order_by(Task.created_at.desc()).limit(1)
                
                res = await db.execute(stmt)
                task = res.scalar_one_or_none()
                if not task:
                    return f"No pending task found containing '{keyword}'." if language == "en" else f"Không tìm thấy công việc nào đang chờ chứa từ khóa '{keyword}'."
                
                task.status = "completed"
                await db.commit()
                return f"Marked task '{task.title}' as completed." if language == "en" else f"Đã đánh dấu xong công việc '{task.title}'."

            elif args_str.startswith("--delete "):
                keyword = args_str.replace("--delete ", "", 1).strip()
                if not keyword:
                    return "Please provide a keyword." if language == "en" else "Vui lòng nhập từ khóa công việc."
                
                stmt = select(Task).where(
                    Task.user_id == user_id,
                    Task.is_deleted == False,
                    Task.title.ilike(f"%{keyword}%")
                ).order_by(Task.created_at.desc()).limit(1)
                
                res = await db.execute(stmt)
                task = res.scalar_one_or_none()
                if not task:
                    return f"No task found containing '{keyword}'." if language == "en" else f"Không tìm thấy công việc chứa từ khóa '{keyword}'."
                
                task.is_deleted = True
                await db.commit()
                return f"Deleted task '{task.title}'." if language == "en" else f"Đã xóa công việc '{task.title}'."

            elif args_str == "--all" or not args_str:
                show_all = args_str == "--all"
                stmt = select(Task).where(
                    Task.user_id == user_id,
                    Task.is_deleted == False
                )
                if not show_all:
                    stmt = stmt.where(Task.status == "pending")
                
                stmt = stmt.order_by(Task.deadline.asc().nulls_last())
                res = await db.execute(stmt)
                tasks = res.scalars().all()

                if not tasks:
                    return "No tasks found." if language == "en" else "Không có công việc nào."
                
                header = "**All Tasks:**\n" if show_all else "**Pending Tasks:**\n"
                if language == "vi":
                    header = "**Tất cả công việc:**\n" if show_all else "**Việc cần làm:**\n"

                response = header
                for t in tasks:
                    status_icon = "✅" if t.status == "completed" else "⏳" if t.status == "in_progress" else "⬜"
                    deadline_str = ""
                    if t.deadline:
                        dt_local = t.deadline.replace(tzinfo=timezone.utc).astimezone(local_tz)
                        deadline_str = f" (Deadline: {dt_local.strftime('%d/%m %H:%M')})"
                    
                    response += f"{status_icon} {t.title}{deadline_str}\n"
                
                return response
            
            else:
                return "Invalid syntax. Type `/task --help` for usage." if language == "en" else "Cú pháp không hợp lệ. Gõ `/task --help` để xem hướng dẫn."
