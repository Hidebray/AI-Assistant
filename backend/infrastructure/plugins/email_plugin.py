import logging
import os
import asyncio
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from backend.infrastructure.plugins.base import BasePlugin
from backend.domain.interfaces.event_bus import IEventBus

logger = logging.getLogger(__name__)

import base64
from email.message import EmailMessage

SCOPES = ['https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/gmail.send']
import sys

if getattr(sys, 'frozen', False):
    appdata_dir = os.getenv('APPDATA', os.path.expanduser("~"))
    BASE_DIR = os.path.join(appdata_dir, "com.aaa.app")
    os.makedirs(BASE_DIR, exist_ok=True)
    CREDENTIALS_FILE = os.path.join(sys._MEIPASS, 'credentials.json')
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')

TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')

class EmailPlugin(BasePlugin):
    """
    Plugin tích hợp Gmail API để đọc email gần đây.
    """
    def __init__(self):
        self.bus = None
        self.is_running = False
        
    def get_metadata(self) -> dict:
        return {
            "name": "email_plugin",
            "version": "1.0",
            "permissions": ["network", "db_read"],
            "config_schema": {"oauth": True},
            "tools": [
                {
                    "name": "read_recent_emails",
                    "description": "Read the most recent incoming emails. Defaults to 5 emails.",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Number of emails to read (default 5)"
                            },
                            "query": {
                                "type": "string",
                                "description": "Gmail search query (e.g. is:unread)"
                            }
                        },
                        "required": []
                    }
                },
                {
                    "name": "send_email",
                    "description": "Compose and send a new email via Gmail.",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "to": {
                                "type": "string",
                                "description": "Recipient email address."
                            },
                            "subject": {
                                "type": "string",
                                "description": "Subject of the email."
                            },
                            "body": {
                                "type": "string",
                                "description": "Body content of the email."
                            }
                        },
                        "required": ["to", "subject", "body"]
                    }
                }
            ]
        }

    async def on_load(self):
        logger.info("[EmailPlugin] Loaded configuration.")

    async def on_start(self, event_bus: IEventBus):
        self.bus = event_bus
        self.is_running = True
        logger.info("[EmailPlugin] Started.")

    async def on_stop(self):
        self.is_running = False
        logger.info("[EmailPlugin] Stopped.")

    def _get_credentials(self):
        if os.path.exists(TOKEN_FILE):
            return Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        return None

    async def execute_tool(self, tool_name: str, payload: dict) -> any:
        if tool_name == "read_recent_emails":
            limit = payload.get("limit", 5)
            query = payload.get("query", "")
            
            creds = self._get_credentials()
            if not creds or not creds.valid:
                return {"error": "Gmail credentials not found. Please connect your Google account in Settings."}
                
            try:
                # Chạy build và execute trong executor để tránh block event loop
                loop = asyncio.get_running_loop()
                def fetch_emails():
                    service = build('gmail', 'v1', credentials=creds, cache_discovery=False)
                    results = service.users().messages().list(userId='me', maxResults=limit, q=query).execute()
                    messages = results.get('messages', [])
                    
                    if not messages:
                        return {"result": "No emails found."}
                        
                    email_summaries = []
                    for msg in messages:
                        msg_data = service.users().messages().get(userId='me', id=msg['id'], format='metadata', metadataHeaders=['Subject', 'From', 'Date']).execute()
                        headers = msg_data.get('payload', {}).get('headers', [])
                        
                        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
                        snippet = msg_data.get('snippet', '')
                        
                        email_summaries.append({
                            "id": msg['id'],
                            "from": sender,
                            "subject": subject,
                            "date": date,
                            "snippet": snippet
                        })
                        
                    return {"emails": email_summaries}

                return await loop.run_in_executor(None, fetch_emails)
            except Exception as e:
                logger.error(f"Error fetching emails: {e}")
                return {"error": f"Failed to fetch emails: {str(e)}"}

        elif tool_name == "send_email":
            to_email = payload.get("to")
            subject = payload.get("subject")
            body = payload.get("body")

            creds = self._get_credentials()
            if not creds or not creds.valid:
                return {"error": "Gmail credentials not found. Please connect your Google account in Settings."}

            try:
                loop = asyncio.get_running_loop()
                def do_send_email():
                    service = build('gmail', 'v1', credentials=creds, cache_discovery=False)
                    message = EmailMessage()
                    message.set_content(body)
                    message['To'] = to_email
                    message['From'] = 'me'
                    message['Subject'] = subject

                    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
                    create_message = {'raw': encoded_message}
                    send_message = (service.users().messages().send(userId="me", body=create_message).execute())
                    return {"status": "Success", "message": f"Successfully sent email to {to_email}."}

                return await loop.run_in_executor(None, do_send_email)
            except Exception as e:
                logger.error(f"Error sending email: {e}")
                return {"status": "Error", "message": f"{str(e)}."}
                
        raise ValueError(f"Unknown tool {tool_name}")
