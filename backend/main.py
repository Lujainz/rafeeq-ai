# main.py
import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from routers.voice import router as voice_router
from database.models import create_tables

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/rafeeq.log", encoding="utf-8")
    ]
)

logger = logging.getLogger(__name__)

# ── Rate limiter ───────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI(title="Rafeeq — رفيق", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ───────────────────────────────────────────────────────
ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://localhost:3000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.mount("/assets", StaticFiles(directory="../frontend"), name="static")
app.include_router(voice_router)

@app.get("/")
async def root():
    return FileResponse("../frontend/index.html")

@app.get("/health")
async def health():
    return JSONResponse({"status": "ok", "service": "rafeeq"})

@app.on_event("startup")
async def startup():
    create_tables()   # create DB tables if they don't exist
    logger.info("رفيق server started ✅")

@app.on_event("shutdown")
async def shutdown():
    logger.info("رفيق server stopped")