from sqlalchemy import create_engine, Column, String, Text, Integer, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import json

# =========================
# Database Config
# =========================

DB_URL = "sqlite:///hospital_memory.db"

engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# =========================
# Tables
# =========================

class UserMemory(Base):
    __tablename__ = "user_memory"

    user_id = Column(String, primary_key=True, index=True)
    data = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    role = Column(String)  # "user" or "assistant"
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


# =========================
# Create Tables
# =========================

Base.metadata.create_all(bind=engine)


# =========================
# DB Dependency
# =========================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# Memory Helpers
# =========================

def get_user_memory(db, user_id):
    record = db.query(UserMemory).filter(UserMemory.user_id == user_id).first()
    if record:
        return json.loads(record.data)
    return {
        "symptoms": [],
        "duration": None,
        "severity": None
    }


def save_user_memory(db, user_id, memory):
    record = db.query(UserMemory).filter(UserMemory.user_id == user_id).first()
    data_json = json.dumps(memory)

    if record:
        record.data = data_json
        record.updated_at = datetime.utcnow()
    else:
        record = UserMemory(user_id=user_id, data=data_json)
        db.add(record)

    db.commit()


# =========================
# Chat Helpers
# =========================

def save_chat(db, user_id, role, message):
    chat = ChatHistory(user_id=user_id, role=role, message=message)
    db.add(chat)
    db.commit()


def get_chat_history(db, user_id, limit=50):
    """Return the last `limit` messages for the user, oldest first."""
    chats = (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == user_id)
        .order_by(ChatHistory.timestamp.asc())
        .limit(limit)
        .all()
    )
    # return as list of dicts for JSON
    return [{"role": c.role, "message": c.message} for c in chats]
