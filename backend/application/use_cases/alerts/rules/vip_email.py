import re
import os
import sys
import sqlite3
import logging
from backend.domain.interfaces.alert_rule import IAlertRule
from backend.application.dtos.alert_dtos import RuleResult, Urgency
from backend.domain.events.base_events import SystemNewEmailEvent
from backend.infrastructure.database.encryption import fernet

logger = logging.getLogger(__name__)

def get_setting_sync(key: str, default: str = "") -> str:
    try:
        # Resolve database path
        if getattr(sys, 'frozen', False):
            appdata_dir = os.getenv('APPDATA', os.path.expanduser("~"))
            db_dir = os.path.join(appdata_dir, "com.aaa.app", "database")
        else:
            db_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../database"))
        
        db_path = os.path.join(db_dir, "app_data.db")
        if not os.path.exists(db_path):
            return default
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT setting_value FROM user_settings WHERE setting_key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            try:
                return fernet.decrypt(row[0].encode("utf-8")).decode("utf-8")
            except Exception:
                return row[0]
    except Exception as e:
        logger.error(f"Error reading setting {key} sync: {e}")
    return default

class VIPEmailRule(IAlertRule):
    def evaluate(self, event_data: any) -> RuleResult:
        if not isinstance(event_data, SystemNewEmailEvent):
            return RuleResult(is_matched=False)
            
        subject = event_data.subject.upper()
        body = event_data.body.upper()
        sender = event_data.sender
        
        # Lấy từ Settings nếu có, fallback về danh sách mặc định
        vip_setting = get_setting_sync("general.vip_emails", "ceo@company.com,boss@company.com,vip@example.com")
        vip_list = [v.strip() for v in vip_setting.split(",") if v.strip()]
        
        email_match = re.search(r'[\w\.-]+@[\w\.-]+', sender)
        email = email_match.group(0).lower() if email_match else sender.strip().lower()
        is_vip = email in [v.lower() for v in vip_list]
        is_urgent = bool(re.search(r'\b(URGENT|ASAP|KHẨN|QUAN TRỌNG)\b', subject))
        
        if is_vip or is_urgent:
            return RuleResult(
                is_matched=True, 
                urgency=Urgency.CRITICAL, 
                weight=95,
                message=f"Email khẩn từ {sender}: {subject}"
            )
        elif "UNSUBSCRIBE" in body:
            return RuleResult(is_matched=True, urgency=Urgency.LOW, weight=95)
            
        return RuleResult(is_matched=False)
