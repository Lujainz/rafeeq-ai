# services/tts.py
import logging
import azure.cognitiveservices.speech as speechsdk
from config import AZURE_SPEECH_KEY, AZURE_SPEECH_REGION, AZURE_TTS_VOICE

logger = logging.getLogger(__name__)

def synthesize_speech(text: str) -> bytes:
    """
    Convert Arabic text to speech using Azure Neural TTS (ar-SA).
    Returns raw audio bytes to send over WebSocket.
    """
    try:
        speech_config = speechsdk.SpeechConfig(
            subscription=AZURE_SPEECH_KEY,
            region=AZURE_SPEECH_REGION
        )
        speech_config.speech_synthesis_voice_name = AZURE_TTS_VOICE

        # No audio_config — Azure returns bytes in result.audio_data directly
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=None
        )

        result = synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            logger.info(f"Azure TTS success — {len(result.audio_data)} bytes, voice: {AZURE_TTS_VOICE}")
            return result.audio_data

        elif result.reason == speechsdk.ResultReason.Canceled:
            detail = result.cancellation_details
            logger.error(f"Azure TTS canceled — {detail.reason}: {detail.error_details}")
            raise RuntimeError(f"Azure TTS failed: {detail.error_details}")

    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise