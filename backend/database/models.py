# database/models.py — bottom section only, replace from engine down
import os
# database/models.py
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DATABASE_URL  # ← this line was missing

Base = declarative_base()
# Use SQLite locally, PostgreSQL in production
# Automatically detected from DATABASE_URL in .env
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}  # needed for SQLite + FastAPI
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10
    )

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)