# services/summarizer.py
import logging
from openai import OpenAI
from sqlalchemy.orm import Session
from config import OPENAI_API_KEY, LLM_MODEL, SUMMARIZE_EVERY
from database.models import ConversationTurn
from database.crud import get_recent_turns, save_memory_fact
from services.vector_memory import store_memory
from utils.encryption import decrypt

logger = logging.getLogger(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)

SUMMARY_PROMPT = """
أنت مساعد يقوم بتلخيص محادثات باللغة العربية.
لديك مجموعة من رسائل المحادثة بين مستخدم كبير في السن ومساعد ذكي اسمه رفيق.

مهمتك:
1. اكتب ملخصاً موجزاً لا يتجاوز 5 جمل يصف أهم ما دار في المحادثة
2. ركز على المعلومات الشخصية، المشاعر، والمواضيع المهمة
3. اكتب بصيغة المخبر عن المستخدم — مثال: "المستخدم تحدث عن..."
4. لا تضف تحليلاً أو تعليقاً، فقط ملخص وقائعي

أعد الملخص فقط بدون أي مقدمة أو خاتمة.
"""

# summarize every N turns
SUMMARIZE_EVERY = 10

def should_summarize(turn_count: int) -> bool:
    """Return True when the turn count hits a multiple of SUMMARIZE_EVERY."""
    return turn_count > 0 and turn_count % SUMMARIZE_EVERY == 0

def summarize_session(user_id: str, db: Session, turn_count: int) -> None:
    """
    Summarize the oldest unsummarized turns for this user,
    store the summary in ChromaDB, and delete the raw turns.
    Fails silently — never breaks the conversation.
    """
    try:
        # fetch the oldest SUMMARIZE_EVERY turns for this user
        raw_turns = (
            db.query(ConversationTurn)
            .filter(ConversationTurn.user_id == user_id)
            .order_by(ConversationTurn.created_at.asc())
            .limit(SUMMARIZE_EVERY)
            .all()
        )

        if len(raw_turns) < SUMMARIZE_EVERY:
            return

        # decrypt and format turns for the LLM
        conversation_text = ""
        for t in raw_turns:
            user_msg      = decrypt(t.user_text)
            assistant_msg = decrypt(t.assistant_text)
            conversation_text += f"المستخدم: {user_msg}\nرفيق: {assistant_msg}\n\n"

        # ask LLM to summarize
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SUMMARY_PROMPT},
                {"role": "user",   "content": conversation_text}
            ],
            temperature=0.3,
            max_tokens=300
        )

        summary = response.choices[0].message.content.strip()

        if not summary:
            logger.warning(f"Summarizer returned empty summary for {user_id[:8]}...")
            return

        logger.info(f"Session summary generated — {len(summary)} chars for {user_id[:8]}...")

        # store summary in ChromaDB as a long-term memory
        store_memory(
            user_id   = user_id,
            text      = summary,
            memory_id = f"summary_{user_id[:8]}_{turn_count}",
            metadata  = {"type": "summary"}
        )

        # save summary as a memory fact in SQLite too
        save_memory_fact(db, user_id, summary, category="session_summary")

        # delete the raw turns that were just summarized
        ids_to_delete = [t.id for t in raw_turns]
        db.query(ConversationTurn).filter(
            ConversationTurn.id.in_(ids_to_delete)
        ).delete(synchronize_session=False)
        db.commit()

        logger.info(f"Deleted {len(ids_to_delete)} raw turns after summarization for {user_id[:8]}...")

    except Exception as e:
        logger.error(f"Summarization failed for {user_id[:8]}...: {e}")
        db.rollback()