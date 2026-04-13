from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
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
    """A verified question stored in the question bank."""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)

    # --- Classification ---
    identifier  = Column(String, unique=True, index=True, nullable=True)   # e.g. PMAT1N0001
    subject     = Column(String, nullable=False, index=True)               # matematicas | lengua | valenciano | ingles | competencia_lectora
    grade       = Column(Integer, nullable=True, index=True)               # 1–6
    bloque      = Column(String, nullable=True, index=True)                # Tema (from temario JSON)
    contenido   = Column(String, nullable=True, index=True)                # Epígrafe
    dificultad  = Column(String, nullable=True, default="normal")          # basica | normal | avanzada

    # --- Content ---
    question_type = Column(String, nullable=False, default="seleccion")    # seleccion | verdadero_falso | pasos
    question      = Column(Text, nullable=False)                           # Enunciado
    options       = Column(Text, nullable=True)                            # JSON: ["Opción A", "Opción B", …]
    answer        = Column(String, nullable=False)                         # Exact correct option string
    explanation         = Column(Text, nullable=True)                            # Legacy generic explanation
    feedback_correct    = Column(Text, nullable=True)                            # Shown when student answers correctly
    feedback_incorrect  = Column(Text, nullable=True)                            # Shown when student answers incorrectly

    # --- Media (paths relative to Render persistent storage) ---
    visual_url  = Column(String, nullable=True)   # Image URL
    audio_url   = Column(String, nullable=True)   # Audio URL

    # --- Metadata ---
    source      = Column(String, nullable=True, default="manual")          # manual | ia_pdf | ia_csv | ia_internet
    is_active   = Column(Boolean, default=True)                            # Soft delete
    is_verified = Column(Boolean, default=False)                           # Quality seal for RAG
    created_by  = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = relationship("User", foreign_keys=[created_by])


class Explanation(Base):
    """A pedagogical explanation linked to a topic or question."""
    __tablename__ = "explanations"

    id = Column(Integer, primary_key=True, index=True)

    # --- Classification ---
    identifier  = Column(String, unique=True, index=True, nullable=True)   # e.g. EMAT1N0001
    subject     = Column(String, nullable=False, index=True)
    grade       = Column(Integer, nullable=True, index=True)
    bloque      = Column(String, nullable=True, index=True)
    contenido   = Column(String, nullable=True, index=True)
    dificultad  = Column(String, nullable=True, default="normal")          # basica | normal | avanzada

    # --- Content ---
    text         = Column(Text, nullable=False)                            # Main explanation text
    steps        = Column(Text, nullable=True)                             # JSON: ["Paso 1…", "Paso 2…"]
    easier_version = Column(Text, nullable=True)                           # Simpler alternative explanation
    examples     = Column(Text, nullable=True)                             # JSON: ["Ejemplo 1…", "Ejemplo 2…"]

    # --- Media ---
    audio_url   = Column(String, nullable=True)
    video_url   = Column(String, nullable=True)
    visual_url  = Column(String, nullable=True)

    # --- Metadata ---
    source      = Column(String, nullable=True, default="manual")          # manual | ia_pdf | ia_csv
    is_active   = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_by  = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = relationship("User", foreign_keys=[created_by])


class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id  = Column(Integer, index=True, nullable=False)
    subject  = Column(String, index=True, nullable=False)
    grade    = Column(Integer, nullable=True)
    bloque   = Column(String, nullable=True)
    contenido = Column(String, nullable=True)
    attempts = Column(Integer, default=0)
    successes = Column(Integer, default=0)
    last_attempt = Column(DateTime, default=datetime.utcnow)


class TopicExplanation(Base):
    """Legacy table kept for backwards compatibility."""
    __tablename__ = "topic_explanations"

    id = Column(Integer, primary_key=True, index=True)
    subject     = Column(String, nullable=False, index=True)
    grade       = Column(Integer, nullable=True)
    bloque      = Column(String, nullable=True)
    contenido   = Column(String, nullable=True, index=True)
    explanation = Column(Text, nullable=False)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
