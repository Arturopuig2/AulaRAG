from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    subject   = Column(String, nullable=False)   # "matematicas", "lengua", "valenciano", "ingles"
    grade     = Column(Integer, nullable=True)    # 1-6, null = all grades
    bloque    = Column(String, nullable=True)     # e.g. "Geometría", "Ortografía"
    contenido = Column(String, nullable=True)     # specific topic within bloque
    question  = Column(Text, nullable=False)      # Question text displayed to user
    options   = Column(Text, nullable=False)      # JSON array: ["Opción A", "Opción B", "Opción C"]
    answer    = Column(String, nullable=False)    # The exact correct option string
    created_at = Column(DateTime, default=datetime.utcnow)


class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    subject = Column(String, index=True, nullable=False)
    grade = Column(Integer, nullable=True)
    bloque = Column(String, nullable=True)
    contenido = Column(String, nullable=True)
    attempts = Column(Integer, default=0)
    successes = Column(Integer, default=0)
    last_attempt = Column(DateTime, default=datetime.utcnow)
