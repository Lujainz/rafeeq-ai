# database/crud.py
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database.models import User, ConversationTurn, MemoryFact
from utils.encryption import encrypt, decrypt

logger = logging.getLogger(__name__)

# ── Users ──────────────────────────────────────────────────────

def get_or_create_user(db: Session, user_id: str) -> User:
    """Return existing user or create a new one."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id)
        db.add(user)
        db.commit()
        logger.info(f"New user created: {user_id[:8]}...")
    else:
        user.last_seen = datetime.utcnow()
        db.commit()
    return user

# ── Conversation turns ─────────────────────────────────────────

def save_turn(db: Session, user_id: str, user_text: str, assistant_text: str) -> None:
    """Save an encrypted conversation turn."""
    try:
        turn = ConversationTurn(
            user_id        = user_id,
            user_text      = encrypt(user_text),       # encrypted before storage
            assistant_text = encrypt(assistant_text),  # encrypted before storage
        )
        db.add(turn)
        db.commit()
        logger.info(f"Turn saved for {user_id[:8]}...")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save turn: {e}")
        raise

def get_recent_turns(db: Session, user_id: str, limit: int = 10) -> list[dict]:
    """Retrieve and decrypt the most recent turns for a user."""
    try:
        turns = (
            db.query(ConversationTurn)
            .filter(ConversationTurn.user_id == user_id)
            .order_by(ConversationTurn.created_at.desc())
            .limit(limit)
            .all()
        )
        # reverse so oldest is first (correct order for LLM context)
        turns = list(reversed(turns))
        return [
            {
                "role": "user",
                "content": decrypt(t.user_text)
            }
            for t in turns
            for _ in [None]  # placeholder — unpacked below
        ] if False else [
            msg
            for t in turns
            for msg in [
                {"role": "user",      "content": decrypt(t.user_text)},
                {"role": "assistant", "content": decrypt(t.assistant_text)},
            ]
        ]
    except Exception as e:
        logger.error(f"Failed to retrieve turns: {e}")
        return []

def delete_old_turns(db: Session, days: int = 30) -> int:
    """Delete raw conversation turns older than N days. Returns count deleted."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    try:
        count = (
            db.query(ConversationTurn)
            .filter(ConversationTurn.created_at < cutoff)
            .delete()
        )
        db.commit()
        logger.info(f"Deleted {count} turns older than {days} days")
        return count
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete old turns: {e}")
        return 0

# ── Memory facts ───────────────────────────────────────────────

def save_memory_fact(db: Session, user_id: str, fact: str, category: str = None) -> None:
    """Save an encrypted long-term memory fact."""
    try:
        memory = MemoryFact(
            user_id  = user_id,
            fact     = encrypt(fact),
            category = category
        )
        db.add(memory)
        db.commit()
        logger.info(f"Memory fact saved for {user_id[:8]}... [{category}]")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save memory fact: {e}")
        raise

def get_memory_facts(db: Session, user_id: str) -> list[str]:
    """Retrieve and decrypt all memory facts for a user."""
    try:
        facts = (
            db.query(MemoryFact)
            .filter(MemoryFact.user_id == user_id)
            .order_by(MemoryFact.created_at.asc())
            .all()
        )
        return [decrypt(f.fact) for f in facts]
    except Exception as e:
        logger.error(f"Failed to retrieve memory facts: {e}")
        return []
    
def get_facts_by_category(db: Session, user_id: str, categories: list[str] = None) -> list[dict]:
    """
    Retrieve decrypted memory facts for a user.
    Optionally filter by category list e.g. ['name', 'health', 'family']
    """
    try:
        query = db.query(MemoryFact).filter(MemoryFact.user_id == user_id)

        if categories:
            query = query.filter(MemoryFact.category.in_(categories))

        facts = query.order_by(MemoryFact.created_at.asc()).all()

        return [
            {"category": f.category, "fact": decrypt(f.fact)}
            for f in facts
        ]
    except Exception as e:
        logger.error(f"Failed to retrieve facts for {user_id[:8]}...: {e}")
        return []
    
def get_turn_count(db: Session, user_id: str) -> int:
    """Return the total number of saved turns for a user."""
    try:
        count = db.query(ConversationTurn)\
                  .filter(ConversationTurn.user_id == user_id)\
                  .count()
        return count
    except Exception as e:
        logger.error(f"Failed to get turn count for {user_id[:8]}...: {e}")
        return 0