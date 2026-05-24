# utils/audio.py
import os
import tempfile
import logging

logger = logging.getLogger(__name__)

# Max audio size — 10MB (~30 min at low bitrate, more than enough)
MAX_AUDIO_BYTES = 10 * 1024 * 1024

def save_bytes_as_webm(audio_bytes: bytes) -> str:
    """Save raw audio bytes to a temp webm file. Returns the file path."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            logger.info(f"Audio saved — {len(audio_bytes)} bytes")
            return tmp.name
    except Exception as e:
        logger.error(f"Failed to save audio bytes: {e}")
        raise

def cleanup_file(path: str) -> None:
    """Delete a temp file safely."""
    try:
        if path and os.path.exists(path):
            os.unlink(path)
    except Exception as e:
        logger.warning(f"Could not delete temp file {path}: {e}")