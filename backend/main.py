# main.py
import logging
import logging.handlers
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routers.voice import router as voice_router

# ── Logging setup ──────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(),                              # terminal
        logging.FileHandler("logs/rafeeq.log", encoding="utf-8")  # file
    ]
)

logger = logging.getLogger(__name__)

# ── App ────────────────────────────────────────────────────────
app = FastAPI(title="Rafeeq — رفيق", version="0.1.0")

app.mount("/static", StaticFiles(directory="../frontend"), name="static")
app.include_router(voice_router)

@app.get("/")
async def root():
    return FileResponse("../frontend/index.html")

@app.on_event("startup")
async def startup():
    logger.info("رفيق server started ✅")

@app.on_event("shutdown")
async def shutdown():
    logger.info("رفيق server stopped")