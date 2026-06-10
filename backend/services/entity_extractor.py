# services/entity_extractor.py
import json
import logging
from openai import OpenAI
from sqlalchemy.orm import Session
from config import OPENAI_API_KEY, LLM_MODEL
from database.models import MemoryFact
from services.vector_memory import store_memory
from utils.encryption import encrypt, decrypt

logger = logging.getLogger(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)

EXTRACTION_PROMPT = """
أنت محلل محادثات. مهمتك استخراج المعلومات الشخصية المهمة من المحادثة.

استخرج فقط المعلومات الواضحة والصريحة. لا تخمن أو تفترض.

أعد النتيجة كـ JSON فقط بهذا الشكل بدون أي نص إضافي:
{
  "facts": [
    {"category": "name", "fact": "اسم المستخدم هو لجين"},
    {"category": "health", "fact": "المستخدم يعاني من ألم في الركبة"},
    {"category": "family", "fact": "ابن المستخدم اسمه أحمد ويسكن في الرياض"},
    {"category": "preference", "fact": "المستخدم يحب القهوة السعودية"}
  ]
}

إذا لم توجد معلومات شخصية مهمة أعد:
{"facts": []}

الفئات المتاحة: name, health, family, preference, location, interest

ملاحظة مهمة: إذا ذكر المستخدم اسمه أو صحح معلومة سابقة،
فهذه المعلومة الجديدة تحل محل القديمة تماماً.
"""

# categories where only ONE fact should ever exist per user
# if a new one comes in, the old one is replaced
SINGLETON_CATEGORIES = {"name", "location"}

def extract_and_store(
    user_id    : str,
    transcript : str,
    reply      : str,
    db         : Session,
    turn_index : int
) -> None:
    """
    Extract personal facts from a conversation turn.
    For singleton categories (name, location), replaces the old fact.
    For multi-value categories (family, health), appends if not duplicate.
    Fails silently — never breaks the conversation.
    """
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": EXTRACTION_PROMPT},
                {"role": "user", "content": (
                    f"المستخدم قال: {transcript}\n"
                    f"رفيق أجاب: {reply}"
                )}
            ],
            temperature=0,
            max_tokens=500
        )

        raw = response.choices[0].message.content.strip()

        try:
            data  = json.loads(raw)
            facts = data.get("facts", [])
        except json.JSONDecodeError:
            logger.warning(f"Entity extractor returned invalid JSON: {raw[:100]}")
            return

        if not facts:
            return

        for i, item in enumerate(facts):
            fact     = item.get("fact", "").strip()
            category = item.get("category", "general").strip()

            if not fact:
                continue

            if category in SINGLETON_CATEGORIES:
                # ── singleton: delete old, insert new ─────────
                _replace_fact(db, user_id, category, fact, turn_index, i)
            else:
                # ── multi-value: only add if not duplicate ────
                _append_fact_if_new(db, user_id, category, fact, turn_index, i)

        logger.info(f"Extracted {len(facts)} facts from turn {turn_index} for {user_id[:8]}...")

    except Exception as e:
        logger.error(f"Entity extraction failed for {user_id[:8]}...: {e}")


def _replace_fact(
    db         : Session,
    user_id    : str,
    category   : str,
    new_fact   : str,
    turn_index : int,
    fact_index : int
) -> None:
    """
    Delete all existing facts of this category for the user,
    then insert the new one. Used for name, location — things
    that can only have one true value at a time.
    """
    try:
        # find existing facts in this category
        existing = (
            db.query(MemoryFact)
            .filter(
                MemoryFact.user_id  == user_id,
                MemoryFact.category == category
            )
            .all()
        )

        # delete old Chroma vectors for these facts
        for old in existing:
            try:
                from services.vector_memory import _get_collection
                col = _get_collection(user_id)
                # delete by searching for matching document
                results = col.get(where={"category": category, "user_id": user_id})
                if results["ids"]:
                    col.delete(ids=results["ids"])
            except Exception as e:
                logger.warning(f"Could not delete old Chroma fact: {e}")

        # delete old SQLite facts
        db.query(MemoryFact).filter(
            MemoryFact.user_id  == user_id,
            MemoryFact.category == category
        ).delete()
        db.commit()

        # insert new fact
        _insert_fact(db, user_id, category, new_fact, turn_index, fact_index)

        logger.info(f"Replaced [{category}] fact for {user_id[:8]}...")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to replace fact [{category}] for {user_id[:8]}...: {e}")


def _append_fact_if_new(
    db         : Session,
    user_id    : str,
    category   : str,
    new_fact   : str,
    turn_index : int,
    fact_index : int
) -> None:
    """
    Add a new fact only if a semantically similar one doesn't
    already exist. Simple check: compare decrypted text directly.
    """
    try:
        existing = (
            db.query(MemoryFact)
            .filter(
                MemoryFact.user_id  == user_id,
                MemoryFact.category == category
            )
            .all()
        )

        # check for near-duplicate text
        for old in existing:
            try:
                old_text = decrypt(old.fact)
                # if 70%+ of words overlap, treat as duplicate
                old_words = set(old_text.split())
                new_words = set(new_fact.split())
                if len(old_words) > 0:
                    overlap = len(old_words & new_words) / len(old_words)
                    if overlap > 0.7:
                        logger.info(f"Skipped duplicate fact [{category}] for {user_id[:8]}...")
                        return
            except Exception:
                continue

        _insert_fact(db, user_id, category, new_fact, turn_index, fact_index)

    except Exception as e:
        logger.error(f"Failed to append fact [{category}] for {user_id[:8]}...: {e}")


def _insert_fact(
    db         : Session,
    user_id    : str,
    category   : str,
    fact       : str,
    turn_index : int,
    fact_index : int
) -> None:
    """Core insert — saves to SQLite and ChromaDB."""
    from database.models import MemoryFact as MF
    from services.vector_memory import store_memory

    # SQLite
    db.add(MF(
        user_id  = user_id,
        fact     = encrypt(fact),
        category = category
    ))
    db.commit()

    # ChromaDB
    store_memory(
        user_id   = user_id,
        text      = fact,
        memory_id = f"fact_{user_id[:8]}_{turn_index}_{fact_index}",
        metadata  = {"type": "fact", "category": category}
    )