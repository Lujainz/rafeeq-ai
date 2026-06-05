# services/vector_memory.py
import logging
import chromadb
from chromadb.config import Settings
from openai import OpenAI
from config import OPENAI_API_KEY, CHROMA_DATA_PATH

logger = logging.getLogger(__name__)

# ── Clients ────────────────────────────────────────────────────

# OpenAI client for generating embeddings
_openai = OpenAI(api_key=OPENAI_API_KEY)

# ChromaDB running locally — persistent on disk
_chroma = chromadb.PersistentClient(
    path=CHROMA_DATA_PATH,
    settings=Settings(anonymized_telemetry=False)
)

# ── Constants ──────────────────────────────────────────────────

EMBEDDING_MODEL  = "text-embedding-3-small"  # fast, cheap, good for Arabic
MAX_MEMORIES     = 500    # max vectors per user — oldest removed when exceeded
TOP_K_RESULTS    = 5      # how many memories to retrieve per query

# ── Collection helpers ─────────────────────────────────────────

def _get_collection(user_id: str):
    """
    Get or create a ChromaDB collection for this user.
    Each user has their own isolated collection — no cross-user leakage.
    Collection name: rafeeq_user_{user_id}
    """
    collection_name = f"rafeeq_user_{user_id}"
    return _chroma.get_or_create_collection(
        name=collection_name,
        metadata={"user_id": user_id, "hnsw:space": "cosine"}
    )

# ── Embedding ──────────────────────────────────────────────────

def _embed(text: str) -> list[float]:
    """Convert text to a vector using OpenAI embeddings."""
    try:
        response = _openai.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise

# ── Store ──────────────────────────────────────────────────────

def store_memory(user_id: str, text: str, memory_id: str, metadata: dict = None) -> None:
    """
    Embed text and store it in the user's Chroma collection.

    memory_id   — unique ID (e.g. "turn_42" or "fact_health_1")
    metadata    — optional dict for filtering (e.g. {"type": "turn", "user_id": user_id})
    """
    try:
        collection = _get_collection(user_id)
        embedding  = _embed(text)

        base_metadata = {"user_id": user_id}
        if metadata:
            base_metadata.update(metadata)

        collection.upsert(
            ids        =[memory_id],
            embeddings =[embedding],
            documents  =[text],           # store original text alongside vector
            metadatas  =[base_metadata]
        )

        # enforce memory cap — remove oldest if over limit
        _enforce_cap(collection, user_id)

        logger.info(f"Memory stored — {user_id[:8]}... | id: {memory_id}")

    except Exception as e:
        logger.error(f"Failed to store memory for {user_id[:8]}...: {e}")
        raise

# ── Retrieve ───────────────────────────────────────────────────

def retrieve_memories(user_id: str, query: str) -> list[str]:
    """
    Find the most semantically relevant memories for a query.
    Returns a list of plain text memories — ready to inject into the LLM prompt.
    """
    try:
        collection = _get_collection(user_id)

        # if the collection is empty, return nothing
        if collection.count() == 0:
            return []

        query_embedding = _embed(query)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(TOP_K_RESULTS, collection.count()),
            where={"user_id": user_id},   # second layer of isolation
        )

        memories = results["documents"][0] if results["documents"] else []
        logger.info(f"Retrieved {len(memories)} memories for {user_id[:8]}...")
        return memories

    except Exception as e:
        logger.error(f"Memory retrieval failed for {user_id[:8]}...: {e}")
        return []   # fail silently — conversation continues without memory

# ── Cap enforcement ────────────────────────────────────────────

def _enforce_cap(collection, user_id: str) -> None:
    """
    If the user's collection exceeds MAX_MEMORIES,
    delete the oldest entries to keep the store lean.
    """
    try:
        count = collection.count()
        if count <= MAX_MEMORIES:
            return

        overflow = count - MAX_MEMORIES
        all_items = collection.get(where={"user_id": user_id})
        ids_to_delete = all_items["ids"][:overflow]

        collection.delete(ids=ids_to_delete)
        logger.info(f"Cap enforced — deleted {overflow} old memories for {user_id[:8]}...")

    except Exception as e:
        logger.warning(f"Cap enforcement failed: {e}")