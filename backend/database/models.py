# database/models.py
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DATABASE_URL

Base = declarative_base()

class User(Base):
    """One row per unique user_id."""
    __tablename__ = "users"

    id          = Column(String(64), primary_key=True)   # the browser-generated user_id
    created_at  = Column(DateTime, default=datetime.utcnow)
    last_seen   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ConversationTurn(Base):
    """
    One row per voice turn.
    user_text and assistant_text are encrypted at rest.
    Raw turns are deleted after 30 days — only summaries are kept long term.
    """
    __tablename__ = "conversation_turns"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    user_id         = Column(String(64), nullable=False, index=True)
    user_text       = Column(Text, nullable=False)       # encrypted
    assistant_text  = Column(Text, nullable=False)       # encrypted
    created_at      = Column(DateTime, default=datetime.utcnow)

class MemoryFact(Base):
    """
    Extracted long-term facts about a user.
    e.g. "user's son is named Ahmed", "user has knee pain"
    Stored encrypted. Never deleted.
    """
    __tablename__ = "memory_facts"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    user_id     = Column(String(64), nullable=False, index=True)
    fact        = Column(Text, nullable=False)            # encrypted
    category    = Column(String(64), nullable=True)       # "family", "health", "preference"
    created_at  = Column(DateTime, default=datetime.utcnow)

# ── Engine + session factory ───────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # test connection before using it
    pool_size=5,             # max 5 persistent connections
    max_overflow=10          # up to 10 extra under heavy load
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all tables if they don't exist. Called on server startup."""
    Base.metadata.create_all(bind=engine)