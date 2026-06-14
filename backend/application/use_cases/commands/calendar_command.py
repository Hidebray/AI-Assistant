import re
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from backend.domain.interfaces.command import ICommand
from backend.infrastructure.database.session import db_manager
from backend.infrastructure.database.models import CalendarEvent

class CalendarCommand(ICommand):
    pattern = r"^/calendar\s*(?P<args>.*)?$"

    def get_help_text(self, lang: str) -> str:
        if lang == "en":
            return "**How to use /calendar:**\n- `/calendar [today | tomorrow | dd/mm]` : View schedule.\n- `/calendar --add [dd/mm HH:MM] [Content]` : Add event.\n- `/calendar --update [Keyword] --to [HH:MM]` : Update event time.\n- `/calendar --delete [Keyword]` : Delete event."
        return "**Cách dùng lệnh /calendar:**\n- `/calendar [today | tomorrow | dd/mm]` : Xem lịch trình.\n- `/calendar --add [dd/mm HH:MM] [Nội dung]` : Thêm sự kiện.\n- `/calendar --update [Từ khóa] --to [HH:MM]` : Đổi giờ sự kiện hôm nay/ngày mai.\n- `/calendar --delete [Từ khóa]` : Xóa sự kiện."

    @property
    def help_text(self) -> str:
        return self.get_help_text("vi")

    async def execute(self, match_dict: dict, user_id: str, language: str = "vi") -> str:
        args_str = match_dict.get('args', '').strip()
        
        if args_str == "--help":
            return self.get_help_text(language)
            
        if args_str.startswith("-") and not args_str.startswith("--"):
            return "Invalid command. Use double dashes (--help, --add, --delete, --update)." if language == "en" else "Lệnh không hợp lệ. Chỉ chấp nhận các cờ có 2 dấu trừ (VD: --help, --add, --delete, --update)."
            
        local_tz = datetime.now().astimezone().tzinfo
        now_local = datetime.now(local_tz)
        
        async with db_manager.session() as db:
            if args_str.startswith("--add "):
                content = args_str.replace("--add ", "", 1).strip()
                match = re.match(r"^(\d{1,2}/\d{1,2})\s+(\d{1,2}:\d{2})\s+(.*)$", content)
                if not match:
                    return "Invalid syntax. Use: /calendar --add dd/mm HH:MM Content" if language == "en" else "Sai cú pháp. Vui lòng dùng: /calendar --add dd/mm HH:MM Noi_dung"
                    
                date_part, time_part, title = match.groups()
                try:
                    day, month = map(int, date_part.split('/'))
                    hour, minute = map(int, time_part.split(':'))
                    year = now_local.year if month >= now_local.month else now_local.year + 1
                    
                    start_local = datetime(year, month, day, hour, minute, tzinfo=local_tz)
                    start_utc = start_local.astimezone(timezone.utc).replace(tzinfo=None)
                    end_utc = start_utc + timedelta(hours=1)
                except ValueError:
                    return "Invalid date/time format." if language == "en" else "Định dạng ngày/giờ không hợp lệ."
                    
                event = CalendarEvent(
                    user_id=user_id,
                    title=title,
                    start_time=start_utc,
                    end_time=end_utc,
                    source_origin="offline_calendar",
                    is_deleted=False
                )
                db.add(event)
                await db.commit()
                return f"Added event: '{title}' at {time_part} on {date_part}." if language == "en" else f"Đã thêm sự kiện: '{title}' vào lúc {time_part} ngày {date_part}."
                
            elif args_str.startswith("--delete "):
                keyword = args_str.replace("--delete ", "", 1).strip()
                if not keyword:
                    return "Please provide a keyword to delete (e.g., /calendar --delete meeting)." if language == "en" else "Vui lòng nhập từ khóa cần xóa (VD: /calendar --delete Hop team)."
                    
                from sqlalchemy import update
                stmt = select(CalendarEvent).where(
                    CalendarEvent.user_id == user_id,
                    CalendarEvent.is_deleted == False,
                    CalendarEvent.title.ilike(f"%{keyword}%")
                )
                res = await db.execute(stmt)
                events = res.scalars().all()
                if not events:
                    return f"No events found containing keyword '{keyword}'." if language == "en" else f"Không tìm thấy sự kiện nào chứa từ khóa '{keyword}'."
                    
                for e in events:
                    e.is_deleted = True
                await db.commit()
                return f"Deleted {len(events)} event(s) containing keyword '{keyword}'." if language == "en" else f"Đã xóa {len(events)} sự kiện chứa từ khóa '{keyword}'."
                
            elif args_str.startswith("--update "):
                content = args_str.replace("--update ", "", 1).strip()
                if " --to " not in content:
                    return "Invalid syntax. Use: /calendar --update Keyword --to HH:MM" if language == "en" else "Sai cú pháp. Vui lòng dùng: /calendar --update Tu_khoa --to HH:MM"
                    
                keyword, new_time_str = content.split(" --to ", 1)
                keyword = keyword.strip()
                new_time_str = new_time_str.strip()
                
                try:
                    hour, minute = map(int, new_time_str.split(':'))
                except ValueError:
                    return "Invalid time format (HH:MM)." if language == "en" else "Định dạng giờ không hợp lệ (HH:MM)."
                    
                stmt = select(CalendarEvent).where(
                    CalendarEvent.user_id == user_id,
                    CalendarEvent.is_deleted == False,
                    CalendarEvent.title.ilike(f"%{keyword}%")
                ).order_by(CalendarEvent.start_time.desc()).limit(1)
                
                res = await db.execute(stmt)
                event = res.scalar_one_or_none()
                if not event:
                    return f"No events found containing keyword '{keyword}' to update." if language == "en" else f"Không tìm thấy sự kiện nào chứa từ khóa '{keyword}' để cập nhật."
                    
                old_start_utc = event.start_time.replace(tzinfo=timezone.utc)
                old_start_local = old_start_utc.astimezone(local_tz)
                new_start_local = old_start_local.replace(hour=hour, minute=minute)
                new_start_utc = new_start_local.astimezone(timezone.utc).replace(tzinfo=None)
                
                event.start_time = new_start_utc
                event.end_time = new_start_utc + timedelta(hours=1)
                await db.commit()
                return f"Updated event '{event.title}' to {new_time_str}." if language == "en" else f"Đã cập nhật sự kiện '{event.title}' sang {new_time_str}."

            date_str = args_str.lower()
            if not date_str or date_str == 'today':
                target_start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
            elif date_str == 'tomorrow':
                target_start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            elif '/' in date_str:
                try:
                    day, month = map(int, date_str.split('/'))
                    year = now_local.year if month >= now_local.month else now_local.year + 1
                    target_start_local = datetime(year, month, day, tzinfo=local_tz)
                except ValueError:
                    return "Invalid date format. Please use dd/mm or 'today', 'tomorrow'." if language == "en" else "Định dạng ngày không hợp lệ. Vui lòng dùng dd/mm hoặc 'today', 'tomorrow'."
            else:
                return "Invalid syntax. Type `/calendar --help` for usage." if language == "en" else "Cú pháp không hợp lệ. Gõ `/calendar --help` để xem hướng dẫn."
                
            target_end_local = target_start_local + timedelta(days=1)
            
            target_start_utc = target_start_local.astimezone(timezone.utc).replace(tzinfo=None)
            target_end_utc = target_end_local.astimezone(timezone.utc).replace(tzinfo=None)
            
            stmt = select(CalendarEvent).where(
                CalendarEvent.user_id == user_id,
                CalendarEvent.start_time >= target_start_utc,
                CalendarEvent.start_time < target_end_utc,
                CalendarEvent.is_deleted == False
            ).order_by(CalendarEvent.start_time.asc())
            
            result = await db.execute(stmt)
            events = result.scalars().all()
            
            display_date = target_start_local.strftime("%d/%m/%Y")
            if not events:
                return f"No schedule for {display_date}." if language == "en" else f"Không có lịch trình nào cho ngày {display_date}."
                
            response = f"**Schedule for {display_date}:**\n" if language == "en" else f"**Lịch trình {display_date}:**\n"
            for e in events:
                dt_utc = e.start_time.replace(tzinfo=timezone.utc)
                dt_local = dt_utc.astimezone(local_tz)
                local_time = dt_local.strftime("%H:%M")
                
                title_display = e.title
                if e.source == "auto_email":
                    title_display = f"[{e.title} (Auto)](auto-email-event)"
                
                response += f"- **{local_time}**: {title_display}\n"
            return response
