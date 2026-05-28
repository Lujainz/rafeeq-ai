# services/entity_extractor.py
import json
import logging
from openai import OpenAI
from config import OPENAI_API_KEY, LLM_MODEL
from services.vector_memory import store_memory
from database.crud import save_memory_fact
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)

EXTRACTION_PROMPT = """
أنت محلل محادثات. مهمتك استخراج المعلومات الشخصية المهمة من المحادثة.

استخرج فقط المعلومات الواضحة والصريحة. لا تخمن أو تفترض.

أعد النتيجة كـ JSON فقط بهذا الشكل بدون أي نص إضافي:
{
  "facts": [
    {"category": "name", "fact": "اسم المستخدم هو خالد"},
    {"category": "health", "fact": "المستخدم يعاني من ألم في الركبة"},
    {"category": "family", "fact": "ابن المستخدم اسمه أحمد ويسكن في الرياض"},
    {"category": "preference", "fact": "المستخدم يحب القهوة السعودية"}
  ]
}

إذا لم توجد معلومات شخصية مهمة أعد:
{"facts": []}

الفئات المتاحة: name, health, family, preference, location, interest
"""

def extract_and_store(
    user_id: str,
    transcript: str,
    reply: str,
    db: Session,
    turn_index: int
) -> None:
    """
    Extract personal facts from a conversation turn and store them
    in both SQLite (encrypted) and ChromaDB (as searchable vectors).
    Runs after every turn — fails silently so it never breaks the conversation.
    """
    try:
        # ask the LLM to extract facts from this turn
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": EXTRACTION_PROMPT},
                {"role": "user", "content": (
                    f"المستخدم قال: {transcript}\n"
                    f"رفيق أجاب: {reply}"
                )}
            ],
            temperature=0,        # deterministic — we want consistent extraction
            max_tokens=500
        )

        raw = response.choices[0].message.content.strip()

        # safely parse JSON
        try:
            data  = json.loads(raw)
            facts = data.get("facts", [])
        except json.JSONDecodeError:
            logger.warning(f"Entity extractor returned invalid JSON: {raw[:100]}")
            return

        if not facts:
            logger.info(f"No entities found in turn {turn_index} for {user_id[:8]}...")
            return

        # store each fact separately
        for i, item in enumerate(facts):
            fact     = item.get("fact", "").strip()
            category = item.get("category", "general").strip()

            if not fact:
                continue

            # 1 — save encrypted to SQLite for structured access
            save_memory_fact(db, user_id, fact, category)

            # 2 — embed and store in ChromaDB for semantic search
            store_memory(
                user_id   = user_id,
                text      = fact,
                memory_id = f"fact_{user_id[:8]}_{turn_index}_{i}",
                metadata  = {"type": "fact", "category": category}
            )

        logger.info(f"Extracted {len(facts)} facts from turn {turn_index} for {user_id[:8]}...")

    except Exception as e:
        # never crash the conversation because of extraction failure
        logger.error(f"Entity extraction failed for {user_id[:8]}...: {e}")