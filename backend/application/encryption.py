import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)

_fernet_instance = None

def get_fernet() -> Fernet:
    global _fernet_instance
    if _fernet_instance is None:
        from dotenv import load_dotenv
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        load_dotenv(env_path)
        
        dev_mode = os.getenv("DEV_MODE", "false").lower() == "true"
        secret_key = os.getenv("SECRET_KEY")
        if not secret_key:
            if dev_mode:
                logger.warning("SECRET_KEY not found in environment, falling back to a default insecure key.")
                secret_key = "default-insecure-key-for-development"
            else:
                logger.warning("SECRET_KEY not found, using standalone desktop fallback.")
                secret_key = "desktop_standalone_secure_fallback_key_for_local_use_only"
        
        salt_str = os.getenv("ENCRYPTION_SALT")
        if not salt_str:
            if dev_mode:
                logger.warning("ENCRYPTION_SALT not found, using dev fallback.")
                salt_str = "ai-assistant-dev-salt"
            else:
                logger.warning("ENCRYPTION_SALT not found, using standalone desktop fallback.")
                salt_str = "ai-assistant-standalone-salt"
                
        # We need a 32 url-safe base64-encoded byte string for Fernet.
        # We use PBKDF2 to derive a 32-byte key from the SECRET_KEY string.
        salt = salt_str.encode("utf-8")
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode("utf-8")))
        _fernet_instance = Fernet(key)
    
    return _fernet_instance

def encrypt_value(value: str) -> str:
    """Mã hoá chuỗi đầu vào sử dụng Fernet."""
    if not value:
        return value
    f = get_fernet()
    encrypted_bytes = f.encrypt(value.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")

def decrypt_value(encrypted_value: str) -> str:
    """Giải mã chuỗi Fernet."""
    if not encrypted_value:
        return encrypted_value
    f = get_fernet()
    try:
        decrypted_bytes = f.decrypt(encrypted_value.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to decrypt value: {e}")
        return "" # Hoặc raise exception tùy thiết kế
