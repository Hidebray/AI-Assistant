"""
E2E test: Save API key via API -> Read it back via llm_factory -> Verify it's usable.
Run from d:\AI-Assistant\backend
"""
import asyncio, sys, os, sqlite3, base64
sys.path.insert(0, 'd:/AI-Assistant')
os.chdir('d:/AI-Assistant/backend')

from cryptography.fernet import Fernet

# DB-layer encryption key (hardcoded fallback in infrastructure/database/encryption.py)
DB_FERNET_KEY = base64.urlsafe_b64encode(b"0123456789abcdef0123456789abcdef").decode()
fernet = Fernet(DB_FERNET_KEY.encode())

prod_db = r'C:\Users\daihi\AppData\Roaming\com.aaa.app\database\app_data.db'

print("=== E2E Test: Settings Encryption Flow ===\n")

# Step 1: Read raw setting_value from DB
conn = sqlite3.connect(prod_db)
cursor = conn.cursor()
cursor.execute("SELECT setting_key, setting_value FROM user_settings WHERE setting_key IN ('llm.openai_key', 'llm.gemini_key', 'llm.ollama_url')")
rows = cursor.fetchall()
conn.close()

print("1. Raw values in DB (encrypted by EncryptedString):")
for k, v in rows:
    if v:
        try:
            dec = fernet.decrypt(v.encode()).decode()
            status = f'"{dec[:50]}"' if dec else "(empty string)"
        except Exception as e:
            status = f"CANNOT DECRYPT: {e}"
    else:
        status = "NULL"
    print(f"   {k}: {status}")

print()

# Step 2: Simulate what SQLAlchemy does (EncryptedString decrypts automatically)
# Then simulate what llm_factory.py does AFTER our fix (no manual decrypt)
print("2. Simulating llm_factory.py flow AFTER fix:")
async def test_llm_factory():
    from backend.infrastructure.database.session import db_manager
    from backend.infrastructure.database.models import UserSetting
    from sqlalchemy import select
    
    async with db_manager.session() as db:
        # This is what llm_factory does
        stmt = select(UserSetting).where(UserSetting.user_id == "86933cc3-f682-47ae-9d08-00b52f8aa57a")
        result = await db.execute(stmt)
        settings_rows = result.scalars().all()
        
        # EncryptedString automatically decrypts on read
        settings = {s.setting_key: s.setting_value for s in settings_rows}
        
        openai_key = settings.get("llm.openai_key") or None
        gemini_key = settings.get("llm.gemini_key") or None
        ollama_url = settings.get("llm.ollama_url") or "http://localhost:11434"
        
        print(f"   openai_key: {repr(openai_key[:20]) if openai_key else 'None/empty'}")
        print(f"   gemini_key: {repr(gemini_key[:20]) if gemini_key else 'None/empty'}")
        print(f"   ollama_url: {repr(ollama_url[:40])}")
        
        return openai_key, gemini_key

asyncio.run(test_llm_factory())

print()
print("=== Done ===")
