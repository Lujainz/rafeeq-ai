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
CHROMA_DATA_PATH: str = os.getenv("CHROMA_DATA_PATH", "./chroma_data")

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

# ── TTS ───────────────────────────────────────────────────────
AZURE_TTS_VOICE: str = "ar-SA-ZariyahNeural"
ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "")
if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY is missing from .env")

# ── STT ───────────────────────────────────────────────────────
STT_MODEL: str = "whisper-1"
STT_LANGUAGE: str = "ar"

# ── Memory ────────────────────────────────────────────────────
SUMMARIZE_EVERY: int = int(os.getenv("SUMMARIZE_EVERY", "10"))
MAX_HISTORY_TURNS: int = 20

# ── System prompt ─────────────────────────────────────────────
SYSTEM_PROMPT: str = (
    "أنت رفيق، مساعد صوتي ذكي ودود. تتحدث مع مستخدمين كبار في السن "
    "في المملكة العربية السعودية عبر الصوت فقط.\n\n"

    "قواعد صارمة يجب اتباعها دائماً:\n"
    "1. لا تستخدم أبداً أي تنسيق نصي مثل النجوم ** أو الشرطات - أو الأرقام المرقمة "
    "أو العناوين أو أي رموز خاصة. الرد يُقرأ بصوت عالٍ لذلك يجب أن يكون نثراً طبيعياً فقط.\n"
    "2. تحدث بأسلوب المحادثة العادية، كأنك تتكلم مع شخص وجهاً لوجه.\n"
    "3. ردودك قصيرة وواضحة، جملتان أو ثلاث كحد أقصى في كل رد.\n"
    "4. كن دقيقاً ومتأكداً من المعلومات التي تقدمها. إذا لم تكن متأكداً من شيء "
    "قل ذلك بصراحة بدلاً من تقديم معلومات خاطئة.\n"
    "5. استخدم اللهجة السعودية البسيطة والمفهومة، وليس الفصحى الرسمية.\n"
    "6. كن دافئاً وصبوراً ومحترماً في كل وقت.\n"
    "7. إذا طُلب منك تعداد أشياء، اذكرها في جملة واحدة مفصولة بفواصل، "
    "وليس كقائمة مرقمة."
)