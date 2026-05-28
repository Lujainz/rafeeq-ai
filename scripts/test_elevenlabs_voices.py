# scripts/test_elevenlabs_voices.py
# Run this once to find the best Arabic-sounding voice
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

# Best voices for Arabic based on community testing
voices_to_test = {
    "a"   : "fkqevZRU7Xj52dY1CTkq",
}

test_text = "السلام عليكم، أنا رفيق، مساعدك الصوتي. كيف حالك اليوم؟"

for name, voice_id in voices_to_test.items():
    print(f"Testing: {name} ({voice_id})")
    audio = client.text_to_speech.convert(
        voice_id=voice_id,
        text=test_text,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    filename = f"test_{name}.mp3"
    with open(filename, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    print(f"Saved: {filename}")

print("\nListen to each file and pick the best one.")
print("Then update ELEVENLABS_VOICE_ID in your .env with that voice's ID.")