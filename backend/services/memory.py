import logging
from config import MAX_HISTORY_TURNS

logger = logging.getLogger(__name__)

# In-memory store: { user_id: [{"role": ..., "content": ...}] }
_store: dict[str, list[dict]] = {}

def get_history(user_id: str) -> list[dict]:
    """Return conversation history for a user."""
    return _store.get(user_id, [])

def add_turn(user_id: str, user_text: str, assistant_text: str) -> None:
    """Append a user+assistant turn and trim to max history."""
    if user_id not in _store:
        _store[user_id] = []

    _store[user_id].append({"role": "user", "content": user_text})
    _store[user_id].append({"role": "assistant", "content": assistant_text})

    # Keep only the last N messages to avoid token bloat
    if len(_store[user_id]) > MAX_HISTORY_TURNS:
        _store[user_id] = _store[user_id][-MAX_HISTORY_TURNS:]

    logger.debug(f"Memory updated for {user_id} — {len(_store[user_id])} messages in history")

def clear_history(user_id: str) -> None:
    """Clear a user's conversation history."""
    _store.pop(user_id, None)
    logger.info(f"Memory cleared for {user_id}")