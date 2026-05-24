
import logging
from openai import OpenAI
from config import OPENAI_API_KEY, LLM_MODEL, SYSTEM_PROMPT

logger = logging.getLogger(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)

def get_reply(user_text: str, history: list[dict]) -> str:
    """Non-streaming reply — kept for testing."""
    try:
        messages = (
            [{"role": "system", "content": SYSTEM_PROMPT}]
            + history
            + [{"role": "user", "content": user_text}]
        )
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages
        )
        reply = response.choices[0].message.content.strip()
        logger.info(f"LLM reply: {reply}")
        return reply
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise

def stream_reply_sentences(user_text: str, history: list[dict]):
    """
    Stream GPT-4o and yield one complete sentence at a time.
    Uses stream=True (classic API) — stable across SDK versions.
    """
    messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + history
        + [{"role": "user", "content": user_text}]
    )

    SENTENCE_ENDINGS = {".", "!", "?", "،", "؟", "!"}
    buffer = ""
    full_reply = ""

    try:
        stream = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            stream=True        # ← classic streaming, no context manager
        )

        for chunk in stream:
            # skip chunks with no content
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content
            if not delta:
                continue

            buffer += delta
            full_reply += delta

            # yield complete sentences as they form
            while True:
                # find the earliest sentence boundary in buffer
                earliest = -1
                for i, char in enumerate(buffer):
                    if char in SENTENCE_ENDINGS:
                        earliest = i
                        break

                if earliest == -1:
                    break  # no sentence boundary yet, keep buffering

                sentence = buffer[:earliest + 1].strip()
                buffer = buffer[earliest + 1:]

                if sentence:
                    logger.info(f"LLM sentence: {sentence}")
                    yield sentence, False

        # yield whatever is left after the stream ends
        if buffer.strip():
            yield buffer.strip(), True
        else:
            yield "", True

        logger.info(f"LLM full reply: {full_reply.strip()}")

    except Exception as e:
        logger.error(f"LLM streaming failed: {e}")
        raise