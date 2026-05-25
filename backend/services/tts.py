# services/tts.py
import logging
import azure.cognitiveservices.speech as speechsdk
from config import AZURE_SPEECH_KEY, AZURE_SPEECH_REGION, AZURE_TTS_VOICE

logger = logging.getLogger(__name__)

def synthesize_speech(text: str) -> bytes:
    """
    Convert Arabic text to speech using Azure Neural TTS with SSML.
    SSML gives us control over speed, pitch, and speaking style.
    """
    try:
        speech_config = speechsdk.SpeechConfig(
            subscription=AZURE_SPEECH_KEY,
            region=AZURE_SPEECH_REGION
        )

        # output format — 24kHz gives noticeably better audio quality
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio24Khz96KBitRateMonoMp3
        )

        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=None
        )

        # SSML gives fine control over how the voice sounds
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"
               xmlns:mstts="http://www.w3.org/2001/mstts"
               xml:lang="ar-SA">
          <voice name="{AZURE_TTS_VOICE}">
            <mstts:express-as style="general" styledegree="1.0">
              <prosody rate="-5%" pitch="-2%">
                {text}
              </prosody>
            </mstts:express-as>
          </voice>
        </speak>
        """

        result = synthesizer.speak_ssml_async(ssml.strip()).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            logger.info(f"TTS success — {len(result.audio_data)} bytes")
            return result.audio_data

        elif result.reason == speechsdk.ResultReason.Canceled:
            detail = result.cancellation_details
            logger.error(f"TTS canceled — {detail.reason}: {detail.error_details}")
            raise RuntimeError(f"Azure TTS failed: {detail.error_details}")

    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise