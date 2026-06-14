import re
from backend.domain.interfaces.command import ICommand
from backend.infrastructure.database.session import db_manager
from backend.infrastructure.database.models import MemoryNode

class NoteCommand(ICommand):
    pattern = r"^/note\s*(?P<content>.*)?$"

    def get_help_text(self, lang: str) -> str:
        if lang == "en":
            return "**How to use /note:**\n- `/note` : List recent notes.\n- `/note [Content]` : Add a new note.\n- `/note --delete [Keyword]` : Delete notes containing keyword."
        return "**Cách dùng lệnh /note:**\n- `/note` : Xem danh sách ghi chú.\n- `/note [Nội Nội dung]` : Thêm ghi chú mới.\n- `/note --delete [Từ khóa]` : Xóa ghi chú chứa từ khóa."

    @property
    def help_text(self) -> str:
        return self.get_help_text("vi")

    async def execute(self, match_dict: dict, user_id: str, language: str = "vi") -> str:
        note_content = match_dict.get('content', '').strip()
        
        if note_content == "--help":
            return self.get_help_text(language)
            
        if note_content.startswith("-") and not note_content.startswith("--"):
            if language == "en":
                return "Invalid command. Only double dashes are allowed (e.g., --help, --delete)."
            return "Lệnh không hợp lệ. Chỉ chấp nhận các cờ có 2 dấu trừ (VD: --help, --delete)."
            
        async with db_manager.session() as db:
            if not note_content:
                from sqlalchemy import select
                stmt = select(MemoryNode).where(
                    MemoryNode.user_id == user_id,
                    MemoryNode.source_origin == "offline_note"
                ).order_by(MemoryNode.created_at.desc()).limit(10)
                
                result = await db.execute(stmt)
                notes = result.scalars().all()
                if not notes:
                    return "No notes found." if language == "en" else "Không có ghi chú nào."
                
                res = "**Recent Notes:**\n" if language == "en" else "**Danh sách ghi chú gần đây:**\n"
                for n in notes:
                    res += f"- {n.content}\n"
                return res
                
            if note_content.startswith("--delete "):
                keyword = note_content.replace("--delete ", "", 1).strip()
                if not keyword:
                    if language == "en":
                        return "Please enter a keyword to delete (e.g., /note --delete wifi)."
                    return "Vui lòng nhập từ khóa cần xóa (VD: /note --delete wifi)."
                    
                from sqlalchemy import delete
                stmt = delete(MemoryNode).where(
                    MemoryNode.user_id == user_id,
                    MemoryNode.source_origin == "offline_note",
                    MemoryNode.content.ilike(f"%{keyword}%")
                )
                res = await db.execute(stmt)
                await db.commit()
                
                if res.rowcount > 0:
                    if language == "en":
                        return f"Deleted {res.rowcount} note(s) containing '{keyword}'."
                    return f"Đã xóa {res.rowcount} ghi chú chứa từ khóa '{keyword}'."
                else:
                    if language == "en":
                        return f"No notes found containing '{keyword}'."
                    return f"Không tìm thấy ghi chú nào chứa từ khóa '{keyword}'."

            # Default to Create
            node = MemoryNode(
                user_id=user_id,
                context_key="preference",
                source_origin="offline_note",
                content=note_content,
                weight=1.0,
                embedding=None
            )
            db.add(node)
            await db.commit()
            
        if language == "en":
            return f"Note saved: {note_content}"
        return f"Đã lưu ghi chú: {note_content}"
