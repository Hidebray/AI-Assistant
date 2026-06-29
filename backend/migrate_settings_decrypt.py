"""
Migration: Decrypt all user_settings values from EncryptedString back to plaintext.
Run ONCE after switching UserSetting.setting_value from EncryptedString to Text.
"""
import sqlite3, base64, sys
from cryptography.fernet import Fernet, InvalidToken

# The hardcoded key from infrastructure/database/encryption.py
DB_FERNET_KEY = base64.urlsafe_b64encode(b"0123456789abcdef0123456789abcdef").decode()
fernet = Fernet(DB_FERNET_KEY.encode())

dbs = [
    r'C:\Users\daihi\AppData\Roaming\com.aaa.app\database\app_data.db',
    r'd:\AI-Assistant\backend\database\app_data.db',
]

for db_path in dbs:
    print(f"\n=== Migrating: {db_path} ===")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, setting_key, setting_value FROM user_settings")
        rows = cursor.fetchall()
        
        migrated = 0
        skipped = 0
        failed = 0
        
        for row_id, key, val in rows:
            if not val:
                skipped += 1
                continue
            try:
                # Attempt to decrypt (it's EncryptedString ciphertext)
                decrypted = fernet.decrypt(val.encode()).decode()
                cursor.execute("UPDATE user_settings SET setting_value = ? WHERE id = ?", (decrypted, row_id))
                print(f"  ✅ {key}: decrypted -> \"{decrypted[:40]}\"")
                migrated += 1
            except InvalidToken:
                # Already plaintext or encrypted with different key - leave as-is
                print(f"  ⚠️  {key}: not encrypted with DB key, keeping as-is: \"{val[:40]}\"")
                skipped += 1
            except Exception as e:
                print(f"  ❌ {key}: ERROR: {e}")
                failed += 1
        
        conn.commit()
        conn.close()
        print(f"  Result: {migrated} decrypted, {skipped} skipped, {failed} failed")
    except Exception as e:
        print(f"  CANNOT OPEN: {e}")

print("\nMigration complete!")
