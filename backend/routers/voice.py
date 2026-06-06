# routers/voice.py
import re
import logging
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from database.models import SessionLocal
from database.crud import (
    get_or_create_user,
    save_turn,
    get_recent_turns,
    get_facts_by_category,
    get_turn_count
)
from services.stt import transcribe_audio
from services.llm import stream_reply_sentences
from services.tts import synthesize_speech
from services.vector_memory import store_memory, retrieve_memories
from services.entity_extractor import extract_and_store
from services.summarizer import should_summarize, summarize_session
from utils.audio import save_bytes_as_webm, cleanup_file, MAX_AUDIO_BYTES

logger = logging.getLogger(__name__)
router = APIRouter()

USER_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_]{1,64}$')

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# core facts always injected — name, health, family always matter
ALWAYS_INJECT_CATEGORIES = ["name", "health", "family"]

@router.websocket("/ws/{user_id}")
async def voice_endpoint(websocket: WebSocket, user_id: str):

    origin = websocket.headers.get("origin", "")
    if origin and origin not in ALLOWED_ORIGINS:
        logger.warning(f"Rejected connection from origin: {origin}")
        await websocket.close(1008)
        return

    if not USER_ID_PATTERN.match(user_id):
        logger.warning(f"Rejected invalid user_id: {user_id!r}")
        await websocket.close(1008)
        return

    await websocket.accept()
    logger.info(f"Client connected: {user_id[:8]}...")

    with SessionLocal() as db:
    
     try:
        get_or_create_user(db, user_id)

        while True:
            audio_bytes = await websocket.receive_bytes()

            if len(audio_bytes) > MAX_AUDIO_BYTES:
                await websocket.send_json({"type": "error", "message": "الملف الصوتي كبير جداً"})
                continue

            # ── transcribe ────────────────────────────────────
            audio_path = save_bytes_as_webm(audio_bytes)
            try:
                transcript = await asyncio.get_event_loop().run_in_executor(
                 None, transcribe_audio, audio_path
                )
            finally:
                cleanup_file(audio_path)

            if not transcript:
                await websocket.send_json({"type": "error", "message": "لم أسمع شيئاً، حاول مرة أخرى"})
                continue

            await websocket.send_json({"type": "transcript", "text": transcript})

            # ── retrieve memories ─────────────────────────────
            # 1. vector search — contextually relevant past turns
            memories = await asyncio.get_event_loop().run_in_executor(
            None, retrieve_memories, user_id, transcript
          )

            # 2. structured facts — name, health, family always present
            facts = get_facts_by_category(
                db, user_id,
                categories=ALWAYS_INJECT_CATEGORIES
            )

            # ── load recent history ───────────────────────────
            history = get_recent_turns(db, user_id, limit=10)

            # ── stream reply ──────────────────────────────────
            full_reply = ""
            for sentence, is_last in stream_reply_sentences(
                transcript, history, memories, facts
            ):
                if not sentence:
                    continue
                full_reply += sentence + " "
                await websocket.send_json({
                    "type"   : "reply_chunk",
                    "text"   : sentence,
                    "is_last": is_last
                })
                audio_out = await asyncio.get_event_loop().run_in_executor(
                None, synthesize_speech, sentence
                )
                await websocket.send_bytes(audio_out)

            full_reply = full_reply.strip()

            # ── save turn to SQLite ───────────────────────────
            save_turn(db, user_id, transcript, full_reply)

            # ── get turn count ────────────────────────────────
            turn_count = get_turn_count(db, user_id)

            # ── store turn in ChromaDB ────────────────────────
            memory_text = f"المستخدم قال: {transcript} | رفيق أجاب: {full_reply}"
            store_memory(
                user_id   = user_id,
                text      = memory_text,
                memory_id = f"turn_{user_id[:8]}_{turn_count}",
                metadata  = {"type": "turn"}
            )

            # ── extract personal facts ────────────────────────
            await asyncio.get_event_loop().run_in_executor(
             None,
             lambda: extract_and_store(
                 user_id    = user_id,
                 transcript = transcript,
                 reply      = full_reply,
                 db         = db,
                 turn_index = turn_count
             )
            )

            # ── summarize if threshold hit ────────────────────
            if should_summarize(turn_count):
                logger.info(f"Summarizing session at turn {turn_count} for {user_id[:8]}...")
                await asyncio.get_event_loop().run_in_executor(
                 None,
                 lambda: summarize_session(user_id, db, turn_count)
               )

            logger.info(f"Turn {turn_count} complete — {user_id[:8]}...")

     except WebSocketDisconnect:
        logger.info(f"Client disconnected: {user_id[:8]}...")
     except Exception as e:
        logger.error(f"Unexpected error for {user_id[:8]}...: {e}")
        try:
            await websocket.send_json({"type": "error", "message": "حدث خطأ، يرجى المحاولة مرة أخرى"})
        except Exception:
            pass