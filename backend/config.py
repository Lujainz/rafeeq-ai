# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# ── OpenAI ────────────────────────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is missing from .env")

# ── Azure TTS ─────────────────────────────────────────────────
AZURE_SPEECH_KEY: str = os.getenv("AZURE_SPEECH_KEY", "")
AZURE_SPEECH_REGION: str = os.getenv("AZURE_SPEECH_REGION", "")
if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
    raise ValueError("AZURE_SPEECH_KEY or AZURE_SPEECH_REGION is missing from .env")

# ── Database ──────────────────────────────────────────────────
DATABASE_URL: str = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is missing from .env")

# ── ChromaDB ──────────────────────────────────────────────────
CHROMA_HOST: str = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", "8001"))

# ── Encryption ────────────────────────────────────────────────
ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")
if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY is missing from .env")

SECRET_KEY: str = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY is missing from .env")

# ── Audio ─────────────────────────────────────────────────────
SAMPLE_RATE: int = 16000

# ── LLM ───────────────────────────────────────────────────────
LLM_MODEL: str = "gpt-4o"
MAX_HISTORY_TURNS: int = 20

# ── TTS ───────────────────────────────────────────────────────
AZURE_TTS_VOICE: str = "ar-SA-HamedNeural"

# ── STT ───────────────────────────────────────────────────────
STT_MODEL: str = "whisper-1"
STT_LANGUAGE: str = "ar"

# ── System prompt ─────────────────────────────────────────────
SYSTEM_PROMPT: str = (
    "أنت رفيق، مساعد ذكي ودود ومهتم. تتحدث مع مستخدمين كبار في السن "
    "في المملكة العربية السعودية. استخدم لغة عربية بسيطة وواضحة، "
    "وكن دافئاً وصبوراً ومحترماً. ردودك قصيرة ومفيدة."
)