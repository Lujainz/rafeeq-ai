
# services/llm.py
import logging
from openai import OpenAI
from config import OPENAI_API_KEY, LLM_MODEL, SYSTEM_PROMPT

logger = logging.getLogger(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)

def get_reply(user_text: str, history: list[dict]) -> str:
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
        logger.info(f"LLM reply — {len(reply)} chars")
        return reply
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise

def stream_reply_sentences(user_text: str, history: list[dict]):
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
            stream=True
        )

        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content
            if not delta:
                continue

            buffer += delta
            full_reply += delta

            while True:
                earliest = -1
                for i, char in enumerate(buffer):
                    if char in SENTENCE_ENDINGS:
                        earliest = i
                        break
                if earliest == -1:
                    break
                sentence = buffer[:earliest + 1].strip()
                buffer = buffer[earliest + 1:]
                if sentence:
                    yield sentence, False

        if buffer.strip():
            yield buffer.strip(), True
        else:
            yield "", True

        logger.info(f"LLM stream complete — {len(full_reply)} chars, {len(history)} history turns")

    except Exception as e:
        logger.error(f"LLM streaming failed: {e}")
        raise