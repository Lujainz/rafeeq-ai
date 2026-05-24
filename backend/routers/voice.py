# routers/voice.py
import re
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.stt import transcribe_audio
from services.llm import stream_reply_sentences
from services.tts import synthesize_speech
from services import memory
from utils.audio import save_bytes_as_webm, cleanup_file, MAX_AUDIO_BYTES

logger = logging.getLogger(__name__)
router = APIRouter()

# Only allow alphanumeric + underscores, max 64 chars
USER_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_]{1,64}$')

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    # add your Vercel URL here later: "https://rafeeq.vercel.app"
]

@router.websocket("/ws/{user_id}")
async def voice_endpoint(websocket: WebSocket, user_id: str):

    # 1 — validate origin
    origin = websocket.headers.get("origin", "")
    if origin and origin not in ALLOWED_ORIGINS:
        logger.warning(f"Rejected connection from origin: {origin}")
        await websocket.close(1008)
        return

    # 2 — validate user_id
    if not USER_ID_PATTERN.match(user_id):
        logger.warning(f"Rejected invalid user_id: {user_id!r}")
        await websocket.close(1008)
        return

    await websocket.accept()
    logger.info(f"Client connected: {user_id[:8]}...")

    try:
        while True:
            audio_bytes = await websocket.receive_bytes()

            # 3 — reject oversized payloads
            if len(audio_bytes) > MAX_AUDIO_BYTES:
                logger.warning(f"Oversized audio payload: {len(audio_bytes)} bytes from {user_id[:8]}...")
                await websocket.send_json({"type": "error", "message": "الملف الصوتي كبير جداً"})
                continue

            logger.info(f"Audio received — {len(audio_bytes)} bytes from {user_id[:8]}...")

            # 4 — transcribe
            audio_path = save_bytes_as_webm(audio_bytes)
            try:
                transcript = transcribe_audio(audio_path)
            finally:
                cleanup_file(audio_path)

            if not transcript:
                await websocket.send_json({"type": "error", "message": "لم أسمع شيئاً، حاول مرة أخرى"})
                continue

            await websocket.send_json({"type": "transcript", "text": transcript})

            # 5 — stream reply
            history = memory.get_history(user_id)
            full_reply = ""

            for sentence, is_last in stream_reply_sentences(transcript, history):
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

            memory.add_turn(user_id, transcript, full_reply.strip())
            logger.info(f"Turn complete — {user_id[:8]}...")

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {user_id[:8]}...")
    except Exception as e:
        logger.error(f"Unexpected error for {user_id[:8]}...: {e}")
        try:
            await websocket.send_json({"type": "error", "message": "حدث خطأ، يرجى المحاولة مرة أخرى"})
        except Exception:
            pass