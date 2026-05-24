# routers/voice.py
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.stt import transcribe_audio
from services.llm import stream_reply_sentences
from services.tts import synthesize_speech
from services import memory
from utils.audio import save_bytes_as_wav, cleanup_file

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws/{user_id}")
async def voice_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    logger.info(f"Client connected: {user_id}")

    try:
        while True:
            # 1 — receive audio
            audio_bytes = await websocket.receive_bytes()
            logger.info(f"Audio received: {len(audio_bytes)} bytes from {user_id}")

            # 2 — transcribe
            wav_path = save_bytes_as_wav(audio_bytes)
            try:
                transcript = transcribe_audio(wav_path)
            finally:
                cleanup_file(wav_path)

            if not transcript:
                await websocket.send_json({"type": "error", "message": "لم أسمع شيئاً، حاول مرة أخرى"})
                continue

            await websocket.send_json({"type": "transcript", "text": transcript})

            # 3 — stream reply sentence by sentence
            history = memory.get_history(user_id)
            full_reply = ""

            for sentence, is_last in stream_reply_sentences(transcript, history):
                if not sentence:
                    continue

                full_reply += sentence + " "

                # Send text chunk to UI immediately
                await websocket.send_json({
                    "type": "reply_chunk",
                    "text": sentence,
                    "is_last": is_last
                })

                # Generate and send TTS audio for this sentence right away
                audio_out = synthesize_speech(sentence)
                await websocket.send_bytes(audio_out)

            # 4 — save the full reply to memory once complete
            memory.add_turn(user_id, transcript, full_reply.strip())

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {user_id}")
    except Exception as e:
        logger.error(f"Unexpected error for {user_id}: {e}")
        try:
            await websocket.send_json({"type": "error", "message": "حدث خطأ، يرجى المحاولة مرة أخرى"})
        except Exception:
            pass