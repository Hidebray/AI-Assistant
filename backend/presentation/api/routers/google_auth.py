from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import os
import logging
from google_auth_oauthlib.flow import InstalledAppFlow

router = APIRouter(prefix="/api/google", tags=["google"])
logger = logging.getLogger(__name__)

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.modify'
]
import sys

if getattr(sys, 'frozen', False):
    appdata_dir = os.getenv('APPDATA', os.path.expanduser("~"))
    BASE_DIR = os.path.join(appdata_dir, "com.aaa.app")
    os.makedirs(BASE_DIR, exist_ok=True)
    CREDENTIALS_FILE = os.path.join(sys._MEIPASS, 'credentials.json')
else:
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')

TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')

SUCCESS_MESSAGE = """
<html>
<head>
    <title>Xác thực thành công</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: white; padding: 40px; border-radius: 16px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1); text-align: center; max-width: 400px; }
        .icon { font-size: 48px; margin-bottom: 20px; }
        h1 { color: #0f172a; font-size: 24px; margin-bottom: 12px; margin-top: 0; }
        p { color: #64748b; line-height: 1.5; margin-bottom: 24px; }
        button { background-color: #3b82f6; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: background-color 0.2s; }
        button:hover { background-color: #2563eb; }
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">✅</div>
        <h1>Xác thực thành công!</h1>
        <p>Tài khoản Google của bạn đã được kết nối với Trợ lý AI AAA. Bạn có thể an tâm đóng cửa sổ này.</p>
        <p id="status_msg" style="color: #ef4444; font-size: 14px; display: none; margin-top: 10px;">Trình duyệt của bạn chặn tự động đóng. Vui lòng đóng tab này thủ công (Bấm dấu X).</p>
        <button onclick="closeWindow()">Đóng cửa sổ</button>
    </div>
    <script>
        function closeWindow() {
            window.open('', '_self', '');
            window.close();
            setTimeout(() => {
                document.getElementById('status_msg').style.display = 'block';
            }, 300);
        }
    </script>
</body>
</html>
"""


import wsgiref.util

# Monkey-patch _RedirectWSGIApp to return text/html instead of text/plain
def custom_wsgi_call(self, environ, start_response):
    start_response("200 OK", [("Content-type", "text/html; charset=utf-8")])
    self.last_request_uri = wsgiref.util.request_uri(environ)
    return [self._success_message.encode("utf-8")]

import google_auth_oauthlib.flow
google_auth_oauthlib.flow._RedirectWSGIApp.__call__ = custom_wsgi_call

def trigger_oauth_flow():
    if not os.path.exists(CREDENTIALS_FILE):
        logger.error("credentials.json is missing! Please put it in the backend folder.")
        return
    try:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0, success_message=SUCCESS_MESSAGE)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        logger.info("Google OAuth Flow completed successfully. Token saved.")
    except Exception as e:
        logger.error(f"Error during Google OAuth flow: {e}")

@router.post("/auth")
async def start_google_auth(background_tasks: BackgroundTasks):
    if not os.path.exists(CREDENTIALS_FILE):
        raise HTTPException(status_code=400, detail="Thiếu file credentials.json trên server.")
    
    background_tasks.add_task(trigger_oauth_flow)
    return {"status": "success", "message": "OAuth flow started in background. Please check the browser that opens on the server machine."}

@router.get("/status")
async def get_google_status():
    has_token = os.path.exists(TOKEN_FILE)
    return {"status": "success", "connected": has_token}
