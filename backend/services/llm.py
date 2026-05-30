# services/llm.py
import logging
from openai import OpenAI
from config import OPENAI_API_KEY, LLM_MODEL, SYSTEM_PROMPT

logger = logging.getLogger(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)

def _build_messages(
    user_text : str,
    history   : list[dict],
    memories  : list[str],
    facts     : list[dict] = None
) -> list[dict]:
    """
    Build the full message list for the LLM.

    Structure:
        [system prompt]
        [structured facts block]   ← name, health, family always injected
        [vector memory block]      ← contextually relevant past memories
        [conversation history]
        [current user message]
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # inject structured facts — always available personal info
    if facts:
        facts_block = (
            "معلومات ثابتة تعرفها عن هذا المستخدم:\n"
            + "\n".join(f"- [{f['category']}] {f['fact']}" for f in facts)
        )
        messages.append({"role": "system", "content": facts_block})

    # inject vector memories — contextually relevant past exchanges
    if memories:
        memory_block = (
            "ذكريات ذات صلة بالموضوع الحالي:\n"
            + "\n".join(f"- {m}" for m in memories)
        )
        messages.append({"role": "system", "content": memory_block})

    messages += history
    messages.append({"role": "user", "content": user_text})
    return messages


def get_reply(
    user_text : str,
    history   : list[dict],
    memories  : list[str]       = None,
    facts     : list[dict]      = None
) -> str:
    try:
        messages = _build_messages(user_text, history, memories or [], facts)
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


def stream_reply_sentences(
    user_text : str,
    history   : list[dict],
    memories  : list[str]  = None,
    facts     : list[dict] = None
):
    messages       = _build_messages(user_text, history, memories or [], facts)
    SENTENCE_ENDINGS = {".", "!", "?", "،", "؟", "!"}
    buffer         = ""
    full_reply     = ""

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

        logger.info(
            f"LLM stream — {len(full_reply)} chars | "
            f"{len(memories or [])} memories | "
            f"{len(facts or [])} facts"
        )

    except Exception as e:
        logger.error(f"LLM streaming failed: {e}")
        raise