import logging
from openai import OpenAI
from config import OPENAI_API_KEY, STT_MODEL, STT_LANGUAGE

logger = logging.getLogger(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)

def transcribe_audio(wav_path: str) -> str:
    """
    Send a WAV file to Whisper and return the Arabic transcript.
    Returns empty string if transcription fails.
    """
    try:
        with open(wav_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model=STT_MODEL,
                file=f,
                language=STT_LANGUAGE
            )
        transcript = result.text.strip()
        logger.info(f"STT transcript: {transcript}")
        return transcript
    except Exception as e:
        logger.error(f"STT failed: {e}")
        raise