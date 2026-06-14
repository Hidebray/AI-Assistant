import os
import base64
from cryptography.fernet import Fernet
from sqlalchemy.types import TypeDecorator, Text
from dotenv import load_dotenv

load_dotenv()

# Lấy khóa mã hóa từ biến môi trường hoặc sinh một khóa ngẫu nhiên nếu chạy ở DEV mode
_ENCRYPTION_KEY = os.getenv("DB_ENCRYPTION_KEY")
if not _ENCRYPTION_KEY:
    # Cảnh báo: trong môi trường Production, bắt buộc phải cung cấp khóa bí mật
    _ENCRYPTION_KEY = base64.urlsafe_b64encode(b"0123456789abcdef0123456789abcdef").decode("utf-8")

fernet = Fernet(_ENCRYPTION_KEY.encode("utf-8"))

class EncryptedString(TypeDecorator):
    """
    SQLAlchemy TypeDecorator để tự động mã hóa chuỗi khi lưu vào CSDL
    và giải mã khi lấy ra bằng AES-128-CBC (Fernet).
    """
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            return fernet.decrypt(value.encode("utf-8")).decode("utf-8")
        except Exception:
            # Nếu không thể giải mã (ví dụ dữ liệu cũ chưa mã hoá), trả về nguyên gốc
            return value
