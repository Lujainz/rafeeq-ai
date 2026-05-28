# routers/voice.py
import re
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from database.models import get_db
from database.crud import get_or_create_user, save_turn, get_recent_turns
from services.stt import transcribe_audio
from services.llm import stream_reply_sentences
from services.tts import synthesize_speech
from services.vector_memory import store_memory, retrieve_memories
from services.entity_extractor import extract_and_store
from utils.audio import save_bytes_as_webm, cleanup_file, MAX_AUDIO_BYTES

logger = logging.getLogger(__name__)
router = APIRouter()

USER_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_]{1,64}$')

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

@router.websocket("/ws/{user_id}")
async def voice_endpoint(websocket: WebSocket, user_id: str):

    # validate origin
    origin = websocket.headers.get("origin", "")
    if origin and origin not in ALLOWED_ORIGINS:
        logger.warning(f"Rejected connection from origin: {origin}")
        await websocket.close(1008)
        return

    # validate user_id
    if not USER_ID_PATTERN.match(user_id):
        logger.warning(f"Rejected invalid user_id: {user_id!r}")
        await websocket.close(1008)
        return

    await websocket.accept()
    logger.info(f"Client connected: {user_id[:8]}...")

    db: Session = next(get_db())

    try:
        get_or_create_user(db, user_id)

        while True:
            audio_bytes = await websocket.receive_bytes()

            if len(audio_bytes) > MAX_AUDIO_BYTES:
                logger.warning(f"Oversized payload from {user_id[:8]}...")
                await websocket.send_json({"type": "error", "message": "الملف الصوتي كبير جداً"})
                continue

            # ── transcribe ────────────────────────────────────
            audio_path = save_bytes_as_webm(audio_bytes)
            try:
                transcript = transcribe_audio(audio_path)
            finally:
                cleanup_file(audio_path)

            if not transcript:
                await websocket.send_json({"type": "error", "message": "لم أسمع شيئاً، حاول مرة أخرى"})
                continue

            await websocket.send_json({"type": "transcript", "text": transcript})

            # ── retrieve relevant memories ────────────────────
            # search ChromaDB for past memories related to what the user just said
            memories = retrieve_memories(user_id, transcript)

            # ── load recent conversation history from DB ───────
            history = get_recent_turns(db, user_id, limit=10)

            # ── stream reply with memories injected ───────────
            full_reply = ""
            for sentence, is_last in stream_reply_sentences(transcript, history, memories):
                if not sentence:
                    continue
                full_reply += sentence + " "
                await websocket.send_json({
                    "type": "reply_chunk",
                    "text": sentence,
                    "is_last": is_last
                })
                audio_out = synthesize_speech(sentence)
                await websocket.send_bytes(audio_out)

            full_reply = full_reply.strip()

            # save turn to SQLite
            save_turn(db, user_id, transcript, full_reply)

            # store turn in ChromaDB
            turn_count = db.execute(
                __import__('sqlalchemy').text("SELECT COUNT(*) FROM conversation_turns WHERE user_id = :uid"),
                {"uid": user_id}
            ).scalar()

            memory_text = f"المستخدم قال: {transcript} | رفيق أجاب: {full_reply}"
            store_memory(
                user_id   = user_id,
                text      = memory_text,
                memory_id = f"turn_{user_id[:8]}_{turn_count}",
                metadata  = {"type": "turn"}
            )

            # extract personal facts from this turn
            extract_and_store(
                user_id    = user_id,
                transcript = transcript,
                reply      = full_reply,
                db         = db,
                turn_index = turn_count
            )

            logger.info(f"Turn complete — {user_id[:8]}...")

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {user_id[:8]}...")
    except Exception as e:
        logger.error(f"Unexpected error for {user_id[:8]}...: {e}")
        try:
            await websocket.send_json({"type": "error", "message": "حدث خطأ، يرجى المحاولة مرة أخرى"})
        except Exception:
            pass
    finally:
        db.close()