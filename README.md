# رفيق — Arabic Voice AI Companion
 
A voice-first AI companion designed for elderly users in Saudi Arabia. Speak naturally in Arabic and رفيق listens, remembers, and responds with a native Saudi Arabic voice — no typing required.
 
---
 
## Overview
 
رفيق (Rafeeq) is an accessibility-focused web application that enables natural Arabic voice conversations powered by large language models. The system maintains long-term memory across sessions, learning the user's name, family members, health notes, and personal preferences over time — making every conversation feel continuous and personal.
 
The project targets elderly users who may be uncomfortable with conventional interfaces. The UI is built around a single large microphone button with no menus, no forms, and no typing.
 
---
## Features
 
- Arabic speech recognition via OpenAI Whisper
- Natural conversation powered by GPT-4o with a Saudi Arabic system prompt
- Native Saudi Arabic voice output via Azure Cognitive Services (ar-SA-HamedNeural / ZariyahNeural)
- Long-term contextual memory using ChromaDB vector search and SQLite
- Automatic entity extraction — names, family, health notes, and preferences are stored after every turn
- Session summarization — long conversations are condensed into long-term memories automatically
- Encrypted storage — all conversation content is encrypted at rest using Fernet symmetric encryption
- Elderly-first UI — single mic button, large Arabic text, RTL layout, no page scroll
- Real-time streaming — sentence-by-sentence TTS so responses begin playing immediately
- WebSocket auto-reconnect and connection state management
---


## Tech stack
 
| Layer | Technology |
|---|---|
| Backend | FastAPI, Python 3.11 |
| Speech-to-text | OpenAI Whisper API |
| Language model | GPT-4o |
| Text-to-speech | Azure Cognitive Services (ar-SA neural voices) |
| Vector memory | ChromaDB |
| Structured storage | SQLite (dev) / PostgreSQL (production) |
| Encryption | cryptography — Fernet |
| Rate limiting | slowapi |
| Frontend | Vanilla HTML, CSS, JavaScript (modular) |
| Fonts | Tajawal (Google Fonts) |
 
---

## Running locally
 
**Requirements:** Python 3.10+, a modern browser with microphone access.
 
**1. Clone the repository**
 
```bash
git clone https://github.com/YOUR_USERNAME/rafeeq.git
cd rafeeq
```
 
**2. Create and activate a virtual environment**
 
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux
```
 
**3. Install dependencies**
 
```bash
pip install -r requirements.txt
```
 
**4. Configure environment variables**
 
Copy the example file and fill in your keys:
 
```bash
cp .env.example .env
```

**5. Start the server**
 
```bash
uvicorn main:app --reload
```
 
Open `http://localhost:8000` in your browser. Hold the mic button, speak in Arabic, and release to send.
 
---
## Status
 
| Phase | Description | Status |
|---|---|---|
| Phase 1 | Voice pipeline — STT, LLM, TTS, WebSocket | Complete |
| Phase 2 | Memory system — ChromaDB, entity extraction, summarization | Complete |
| Phase 3 | Frontend redesign — elderly-first UI, RTL, mic animations | Complete |