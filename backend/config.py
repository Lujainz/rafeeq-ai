
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is missing from .env file")

AZURE_SPEECH_KEY: str = os.getenv("AZURE_SPEECH_KEY", "")
AZURE_SPEECH_REGION: str = os.getenv("AZURE_SPEECH_REGION", "")
if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
    raise ValueError("AZURE_SPEECH_KEY or AZURE_SPEECH_REGION is missing from .env file")

# Audio
SAMPLE_RATE: int = 16000

# LLM
LLM_MODEL: str = "gpt-4o"
MAX_HISTORY_TURNS: int = 20

# TTS — Azure
AZURE_TTS_VOICE: str = "ar-SA-HamedNeural"   # swap to ar-SA-ZariyahNeural for female voice

# STT
STT_MODEL: str = "whisper-1"
STT_LANGUAGE: str = "ar"

# System prompt
SYSTEM_PROMPT: str = (
    "أنت رفيق، مساعد ذكي ودود ومهتم. تتحدث مع مستخدمين كبار في السن "
    "في المملكة العربية السعودية. استخدم لغة عربية بسيطة وواضحة، "
    "وكن دافئاً وصبوراً ومحترماً. ردودك قصيرة ومفيدة."
)