# database/models.py
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from config import DATABASE_URL

Base = declarative_base()

# ── Models ─────────────────────────────────────────────────────

class User(Base):
    """One row per unique user_id."""
    __tablename__ = "users"

    id         = Column(String(64), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ConversationTurn(Base):
    """
    One row per voice turn.
    user_text and assistant_text are encrypted at rest.
    Raw turns deleted after 30 days — summaries kept long term.
    """
    __tablename__ = "conversation_turns"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    user_id        = Column(String(64), nullable=False, index=True)
    user_text      = Column(Text, nullable=False)   # encrypted
    assistant_text = Column(Text, nullable=False)   # encrypted
    created_at     = Column(DateTime, default=datetime.utcnow)

class MemoryFact(Base):
    """
    Extracted long-term facts about a user.
    e.g. 'user's son is named Ahmed', 'user has knee pain'
    Stored encrypted. Never deleted.
    """
    __tablename__ = "memory_facts"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(String(64), nullable=False, index=True)
    fact       = Column(Text, nullable=False)        # encrypted
    category   = Column(String(64), nullable=True)  # "family", "health", "preference"
    created_at = Column(DateTime, default=datetime.utcnow)

# ── Engine ─────────────────────────────────────────────────────

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10
    )

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)

def get_db():
    """Yields a DB session and closes it after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all tables if they don't exist. Called on startup."""
    Base.metadata.create_all(bind=engine)