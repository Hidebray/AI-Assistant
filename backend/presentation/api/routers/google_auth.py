from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import os
import logging
from google_auth_oauthlib.flow import InstalledAppFlow

router = APIRouter(prefix="/api/google", tags=["google"])
logger = logging.getLogger(__name__)

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.readonly'
]
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')

def trigger_oauth_flow():
    if not os.path.exists(CREDENTIALS_FILE):
        logger.error("credentials.json is missing! Please put it in the backend folder.")
        return
    try:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
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
