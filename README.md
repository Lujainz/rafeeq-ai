# رفيق — Arabic AI Voice Companion

A voice-first Arabic AI companion designed for elderly users in Saudi Arabia.
Speak naturally in Arabic — رفيق listens, understands, and responds with a native Saudi Arabic voice.

## Features
- Arabic speech recognition (OpenAI Whisper)
- Natural Arabic conversation (GPT-4o)
- Native Saudi Arabic voice (Azure Neural TTS — ar-SA-HamedNeural)
- Persistent memory across sessions
- Elderly-first accessible UI (RTL, large buttons, minimal complexity)

## Tech stack
| Layer | Technology |
|---|---|
| Backend | FastAPI + Python |
| STT | OpenAI Whisper |
| LLM | GPT-4o |
| TTS | Azure Cognitive Services (ar-SA) |
| Memory | SQLite + ChromaDB |
| Frontend | HTML / CSS / Vanilla JS |

## Running locally

1. Clone the repo
2. Create `backend/.env` with your API keys (see `.env.example`)
3. Install dependencies: `pip install -r backend/requirements.txt`
4. Start the server: `cd backend && uvicorn main:app --reload`
5. Open `http://localhost:8000`

## Project status
Phase 1 complete — voice pipeline running.
Phase 2 complete — memory system.
Phase 3 in progress - frontend redesign.