# services/stt.py
import logging
from openai import OpenAI
from config import OPENAI_API_KEY, STT_MODEL, STT_LANGUAGE

logger = logging.getLogger(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)

def transcribe_audio(audio_path: str) -> str:
    try:
        with open(audio_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model=STT_MODEL,
                file=f,
                language=STT_LANGUAGE
            )
        transcript = result.text.strip()
        logger.info(f"STT complete — {len(transcript)} chars")
        return transcript
    except Exception as e:
        logger.error(f"STT failed: {e}")
        raise