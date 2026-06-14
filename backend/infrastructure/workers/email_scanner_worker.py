import logging
import os
import asyncio
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from backend.domain.interfaces.event_bus import IEventBus
from backend.domain.events.base_events import SystemNewEmailEvent, AutonomousSyncEvent
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.infrastructure.database.session import db_manager
from backend.infrastructure.database.models import User, CalendarEvent
from backend.application.use_cases.llm_factory import LLMFactory
from backend.application.dtos.sync_dtos import EmailAnalysisDTO
import aiofiles
from jinja2 import Template
from sqlalchemy import select
from datetime import datetime


logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')

class EmailScannerWorker:
    def __init__(self, event_bus: IEventBus):
        self.event_bus = event_bus
        self.last_checked_history_id = None

    def _get_credentials(self):
        if os.path.exists(TOKEN_FILE):
            return Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        return None

    async def _load_prompt(self, filename: str) -> str:
        prompt_path = os.path.join(
            os.path.dirname(__file__), 
            "../prompts/core", 
            filename
        )
        try:
            async with aiofiles.open(prompt_path, "r", encoding="utf-8") as f:
                return await f.read()
        except FileNotFoundError:
            return "Trích xuất thông tin."

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    def _fetch_emails_from_api_sync(self, creds, limit=5):
        logger.debug("Fetching unread emails from Gmail API (with retry policy)...")
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().messages().list(userId='me', maxResults=limit, q="is:unread").execute()
        messages = results.get('messages', [])
        
        fetched_messages = []
        for msg in messages:
            msg_data = service.users().messages().get(
                userId='me', id=msg['id'], format='metadata', 
                metadataHeaders=['Subject', 'From', 'Date']
            ).execute()
            fetched_messages.append(msg_data)
        return fetched_messages

    async def scan_unread_emails(self):
        """Cronjob: Quét email mới định kỳ và gửi cho AlertEngine đánh giá."""
        creds = self._get_credentials()
        if not creds or not creds.valid:
            logger.debug("EmailScannerWorker: No valid credentials. Skipping.")
            return

        try:
            loop = asyncio.get_running_loop()
            messages_data = await loop.run_in_executor(None, self._fetch_emails_from_api_sync, creds)
            
            if not messages_data:
                return

            async with db_manager.session() as db:
                # Tìm user đầu tiên (mặc định cho desktop app 1 user)
                result = await db.execute(select(User).limit(1))
                user = result.scalars().first()
                if not user:
                    return

                # Khởi tạo LLM Adapter
                llm = await LLMFactory.get_adapter(db, user_id=user.id)
                prompt_raw = await self._load_prompt("email_analysis.prompt.j2")
                template = Template(prompt_raw)
                current_time = datetime.now().astimezone().isoformat()

                for msg_data in messages_data:
                    headers = msg_data.get('payload', {}).get('headers', [])
                    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                    sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                    snippet = msg_data.get('snippet', '')
                    
                    # 1. Phân tích bằng LLM
                    system_prompt = template.render(
                        current_time=current_time,
                        sender=sender,
                        subject=subject,
                        body=snippet
                    )
                    
                    try:
                        analysis: EmailAnalysisDTO = await llm.generate_response(
                            messages=[{"role": "system", "content": system_prompt}],
                            response_format=EmailAnalysisDTO
                        )
                    except Exception as parse_e:
                        logger.error(f"Failed to parse EmailAnalysisDTO: {parse_e}")
                        continue

                    # 2. Xử lý logic Autonomous Sync
                    if analysis.has_event and analysis.event_title and analysis.start_time:
                        # Thêm sự kiện vào Calendar
                        end_time_val = analysis.end_time
                        if not end_time_val:
                            # Default 1 hour later
                            from dateutil import parser
                            from datetime import timedelta
                            try:
                                dt = parser.parse(analysis.start_time)
                                end_time_val = (dt + timedelta(hours=1)).isoformat()
                            except:
                                end_time_val = analysis.start_time

                        new_event = CalendarEvent(
                            user_id=user.id,
                            title=analysis.event_title,
                            description=f"Auto-synced from email: {subject}\n{analysis.summary}",
                            start_time=analysis.start_time,
                            end_time=end_time_val,
                            location=None,
                            source="auto_email",
                            source_id=msg_data.get("id")
                        )
                        db.add(new_event)
                        await db.commit()

                        # Publish AutonomousSyncEvent
                        sync_event = AutonomousSyncEvent(
                            source_origin="email_scanner_worker",
                            status="success",
                            message=f"Đã tự động thêm sự kiện '{analysis.event_title}' vào lịch.",
                            event_title=analysis.event_title,
                            start_time=analysis.start_time
                        )
                        await self.event_bus.publish(sync_event)

                    # 3. Alert nếu URGENT
                    if analysis.is_urgent:
                        event_data = SystemNewEmailEvent(
                            source_origin="email_scanner_worker",
                            status="success",
                            message="New urgent email found",
                            sender=sender,
                            subject=subject,
                            body=analysis.summary
                        )
                        await self.event_bus.publish(event_data)
                    
                    # Mark email as read via Gmail API in the background (mocked here, should use modify API)
                    # logger.info(f"Marking email {msg_data.get('id')} as read...")
                
        except Exception as e:
            logger.error(f"EmailScannerWorker Error: {e}")

