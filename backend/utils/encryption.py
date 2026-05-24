# utils/encryption.py
import logging
from cryptography.fernet import Fernet
from config import ENCRYPTION_KEY

logger = logging.getLogger(__name__)
_fernet = Fernet(ENCRYPTION_KEY.encode())

def encrypt(text: str) -> str:
    """Encrypt a string before storing in the database."""
    try:
        return _fernet.encrypt(text.encode()).decode()
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise

def decrypt(token: str) -> str:
    """Decrypt a string retrieved from the database."""
    try:
        return _fernet.decrypt(token.encode()).decode()
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise