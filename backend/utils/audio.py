import os
import tempfile
import logging

logger = logging.getLogger(__name__)

def save_bytes_as_wav(audio_bytes: bytes) -> str:
    """Save raw audio bytes to a temp WAV file. Returns the file path."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            return tmp.name
    except Exception as e:
        logger.error(f"Failed to save audio bytes to WAV: {e}")
        raise

def cleanup_file(path: str) -> None:
    """Delete a temp file safely."""
    try:
        if path and os.path.exists(path):
            os.unlink(path)
    except Exception as e:
        logger.warning(f"Could not delete temp file {path}: {e}")