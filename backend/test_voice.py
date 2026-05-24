import os
import tempfile
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import pygame
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

SAMPLE_RATE = 16000
DURATION_SECONDS = 6  # how long it records before sending

def record_audio():
    print("\n🎤 جاري الاستماع... تكلم الآن")
    audio = sd.rec(
        int(DURATION_SECONDS * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16"
    )
    sd.wait()
    print("✅ تم التسجيل")
    return audio

def save_wav(audio):
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    write(tmp.name, SAMPLE_RATE, audio)
    return tmp.name

def transcribe(wav_path):
    with open(wav_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language="ar"
        )
    return result.text

def get_response(transcript):
    print(f"\n👤 أنت قلت: {transcript}")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "أنت رفيق، مساعد ذكي ودود ومهتم. تتحدث مع مستخدمين كبار في السن "
                    "في المملكة العربية السعودية. استخدم لغة عربية بسيطة وواضحة، "
                    "وكن دافئاً وصبوراً ومحترماً. ردودك قصيرة ومفيدة."
                )
            },
            {"role": "user", "content": transcript}
        ]
    )
    reply = response.choices[0].message.content
    print(f"\n🤖 رفيق: {reply}")
    return reply

def speak(text):
    response = client.audio.speech.create(
        model="tts-1",
        voice="onyx",
        input=text
    )

    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.write(response.content)   # write bytes directly — no stream_to_file
    tmp.close()                   # close before pygame touches it (Windows requires this)

    pygame.mixer.init()
    pygame.mixer.music.load(tmp.name)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

    pygame.mixer.music.unload()   # release the file before deleting
    os.unlink(tmp.name)

def main():
    print("=" * 40)
    print("  رفيق — مساعدك الصوتي")
    print("=" * 40)
    print("اضغط Enter للتحدث، أو اكتب 'q' للخروج")

    while True:
        user_input = input("\n> ")
        if user_input.strip().lower() == "q":
            print("مع السلامة!")
            break

        audio = record_audio()
        wav_path = save_wav(audio)

        transcript = transcribe(wav_path)
        os.unlink(wav_path)

        if not transcript.strip():
            print("لم أسمع شيئاً، حاول مرة أخرى.")
            continue

        reply = get_response(transcript)
        speak(reply)

if __name__ == "__main__":
    main()