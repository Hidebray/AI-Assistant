import logging
import re
from typing import List
from backend.domain.interfaces.command import ICommand
from backend.application.use_cases.commands.calendar_command import CalendarCommand
from backend.application.use_cases.commands.note_command import NoteCommand
from backend.application.use_cases.commands.task_command import TaskCommand

logger = logging.getLogger(__name__)

class FallbackEngine:
    def __init__(self):
        self.commands: List[ICommand] = []
        self._register_default_commands()

    def _register_default_commands(self):
        self.commands.append(CalendarCommand())
        self.commands.append(NoteCommand())
        self.commands.append(TaskCommand())
        
    def register_command(self, command: ICommand):
        self.commands.append(command)

    async def process(self, content: str, user_id: str, language: str = "vi") -> str:
        """Xử lý các lệnh tĩnh bằng Regex khi đang offline (OCP Architecture)"""
        content = content.strip()
        
        if not content.startswith("/"):
            if language == "en":
                return "Assistant is offline. Please type '/' to use local commands (e.g. /calendar, /note)."
            return "Trợ lý đang mất kết nối mạng. Vui lòng nhập dấu '/' để sử dụng các lệnh cục bộ (VD: /calendar, /note)."

        for cmd in self.commands:
            match = re.match(cmd.pattern, content)
            if match:
                try:
                    return await cmd.execute(match.groupdict(), user_id, language)
                except Exception as e:
                    import traceback
                    err = traceback.format_exc()
                    logger.error(f"Lỗi khi thực thi lệnh offline {cmd.__class__.__name__}: {e}", exc_info=True)
                    try:
                        with open("d:\\AI-Assistant\\backend\\fallback_error.txt", "a", encoding="utf-8") as f:
                            f.write(err + "\n")
                    except:
                        pass
                    if language == "en":
                        return "An error occurred while executing the internal command."
                    return "Đã xảy ra lỗi khi thực thi lệnh nội bộ."

        # Nếu không có command nào khớp
        help_texts = "\n".join([f"- {c.help_text}" for c in self.commands if c.help_text])
        if language == "en":
            return f"Invalid command. Supported commands:\n{help_texts}"
        return f"Lệnh không hợp lệ. Các lệnh hỗ trợ:\n{help_texts}"
