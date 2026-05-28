# services/llm.py
import logging
from openai import OpenAI
from config import OPENAI_API_KEY, LLM_MODEL, SYSTEM_PROMPT

logger = logging.getLogger(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)

def _build_messages(user_text: str, history: list[dict], memories: list[str]) -> list[dict]:
    """
    Build the full message list for the LLM.

    Structure:
        [system prompt]
        [memory block]     ← injected if memories exist, invisible to user
        [conversation history]
        [current user message]
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # inject memories as a system-level context block
    if memories:
        memory_block = (
            "فيما يلي معلومات مهمة تذكرتها عن هذا المستخدم من محادثات سابقة. "
            "استخدمها بشكل طبيعي في ردودك دون الإشارة إلى أنك تقرأ من ملاحظات:\n\n"
            + "\n".join(f"- {m}" for m in memories)
        )
        messages.append({"role": "system", "content": memory_block})

    messages += history
    messages.append({"role": "user", "content": user_text})
    return messages


def get_reply(user_text: str, history: list[dict], memories: list[str] = None) -> str:
    """Non-streaming reply — kept for testing."""
    try:
        messages = _build_messages(user_text, history, memories or [])
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


def stream_reply_sentences(user_text: str, history: list[dict], memories: list[str] = None):
    """
    Stream GPT-4o and yield one complete sentence at a time.
    Memories are injected silently — the user never sees them.
    """
    messages = _build_messages(user_text, history, memories or [])

    SENTENCE_ENDINGS = {".", "!", "?", "،", "؟", "!"}
    buffer     = ""
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

            buffer     += delta
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
                buffer   = buffer[earliest + 1:]
                if sentence:
                    yield sentence, False

        if buffer.strip():
            yield buffer.strip(), True
        else:
            yield "", True

        logger.info(f"LLM stream complete — {len(full_reply)} chars, {len(memories or [])} memories injected")

    except Exception as e:
        logger.error(f"LLM streaming failed: {e}")
        raise