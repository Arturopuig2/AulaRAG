import json
import os
import re

from fastapi import Depends, FastAPI, Form, HTTPException, Request, UploadFile, File, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime

from .rag_engine import get_gemini_response, upload_new_file_to_gemini
from . import models
from .auth import (
    get_current_user,
    get_password_hash,
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_DAYS,
)
from .database import engine, get_db
from datetime import timedelta

# Create DB tables on startup
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Aula RAG AI Assistant")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ── Auth pages ────────────────────────────────────────────────────────────────

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


# ── Auth API ──────────────────────────────────────────────────────────────────

@app.post("/auth/register")
async def register(
    request: Request,
    db: Session = Depends(get_db),
):
    data = await request.json()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # Validate
    if not name:
        raise HTTPException(status_code=400, detail="El nombre es obligatorio")
    email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    if not re.match(email_regex, email):
        raise HTTPException(status_code=400, detail="El correo electrónico no es válido")
    if len(password) < 8 or not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 8 caracteres, una letra y un número")

    # Check uniqueness
    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(status_code=400, detail="Este correo ya está registrado")

    user = models.User(
        email=email,
        name=name,
        hashed_password=get_password_hash(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "name": user.name}


@app.post("/auth/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    email = form_data.username.strip().lower()
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")

    token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS),
    )
    return {"access_token": token, "token_type": "bearer"}


@app.post("/auth/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response


@app.get("/auth/me")
async def me(current_user: models.User = Depends(get_current_user)):
    return {"id": current_user.id, "email": current_user.email, "name": current_user.name, "is_admin": current_user.is_admin}


# ── Main app page ─────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ── Temario API ───────────────────────────────────────────────────────────────

@app.get("/api/temario/{subject}")
async def get_temario(subject: str):
    """Generic endpoint to serve the syllabus JSON for any subject."""
    SUBJECT_FILES = {
        "lengua":              "lengua/temario_lengua.json",
        "matematicas":         "matematicas/temario_matematicas.txt",
        "valenciano":          "valenciano/temario_valenciano.json",
        "ingles":              "ingles/temario_ingles.json",
        "competencia_lectora": "competencia_lectora/temario_competencia_lectora.json",
    }

    relative_path = SUBJECT_FILES.get(subject.lower())
    if not relative_path:
        raise HTTPException(status_code=404, detail=f"Temario not found for subject: '{subject}'")

    base_data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "source_files")
    file_path = os.path.join(base_data_dir, relative_path)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Temario file not found: {relative_path}")
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# ── Chat ──────────────────────────────────────────────────────────────────────

@app.post("/chat")
async def chat_endpoint(
    request: Request,
    message: str = Form(...),
    subject: str = Form("general"),
    course_level: str = Form(""),
    reset_history: bool = Form(False),
    db: Session = Depends(get_db),
):
    # Require authentication
    try:
        current_user = await get_current_user(request, db)
    except HTTPException:
        return JSONResponse({"error": "not_authenticated"}, status_code=401)

    # Update last_seen_at
    current_user.last_seen_at = datetime.utcnow()
    db.commit()

    try:
        # Fetch mastery stats for the current user and subject
        stats_query = db.query(models.UserProgress).filter(
            models.UserProgress.user_id == current_user.id
        )
        if subject != "general":
            stats_query = stats_query.filter(func.lower(models.UserProgress.subject) == subject.lower())
        
        # We only care about weaknesses for the proactive tutoring
        raw_stats = stats_query.all()
        mastery_stats = []
        for s in raw_stats:
            rate = (s.successes / s.attempts) if s.attempts > 0 else 0
            mastery_stats.append({
                "subject": s.subject,
                "bloque": s.bloque,
                "contenido": s.contenido,
                "attempts": s.attempts,
                "rate": round(rate * 100, 1)
            })
        # Sort by rate so the AI sees biggest weaknesses first
        mastery_stats.sort(key=lambda x: x["rate"])
        
        response_text = await get_gemini_response(
            message, subject, course_level, str(current_user.email), 
            reset_history, 
            mastery_stats=mastery_stats[:10] # Top 10 indicators
        )
        return {"response": response_text}
    except Exception as e:
        return {"error": str(e)}


# ── Upload (admin) ────────────────────────────────────────────────────────────

@app.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    subject: str = Form("general"),
    db: Session = Depends(get_db),
):
    current_user = await get_current_user(request, db)
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    import shutil
    if not file.filename.endswith(".pdf"):
        return {"error": "Only PDF files are supported"}

    source_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "source_files", subject)
    os.makedirs(source_dir, exist_ok=True)
    file_path = os.path.join(source_dir, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    success = upload_new_file_to_gemini(file_path, subject)
    if success:
        return {"filename": file.filename, "status": "Successfully uploaded and indexed by Gemini"}
    else:
        return {"error": "Failed to index file in Gemini API"}



# ── Question Bank ─────────────────────────────────────────────────────────────

from pydantic import BaseModel
from typing import Optional, List
import random as _random

class QuestionIn(BaseModel):
    subject: str
    grade: Optional[int] = None
    bloque: Optional[str] = None
    contenido: Optional[str] = None
    question: str
    options: List[str]
    answer: str

class AnswerCheck(BaseModel):
    question_id: int
    selected_option: str


@app.get("/questions/random")
async def get_random_question(
    request: Request,
    subject: str,
    grade: Optional[int] = None,
    bloque: Optional[str] = None,
    contenido: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Return a random question from the bank, filtered by subject/grade/bloque/contenido."""
    try:
        current_user = await get_current_user(request, db)
    except HTTPException:
        return JSONResponse({"error": "not_authenticated"}, status_code=401)

    q = db.query(models.Question).filter(func.lower(models.Question.subject) == subject.lower())
    if grade is not None:
        q = q.filter((models.Question.grade == grade) | (models.Question.grade == None))
    if bloque:
        q = q.filter(func.lower(models.Question.bloque) == bloque.lower())
    if contenido:
        q = q.filter(func.lower(models.Question.contenido) == contenido.lower())

    # Use func.random() for efficient selection at DB level
    picked = q.order_by(func.random()).first()
    
    if not picked:
        return JSONResponse({"error": "no_questions", "detail": "No hay preguntas para este filtro."}, status_code=404)

    return {
        "id": picked.id,
        "question": picked.question,
        "options": json.loads(picked.options),
        # NOTE: answer is intentionally NOT returned to the client
    }


@app.post("/questions/check")
async def check_answer(
    request: Request,
    body: AnswerCheck,
    db: Session = Depends(get_db),
):
    """Server-side answer evaluation. Returns {correct: bool, answer: str}."""
    try:
        current_user = await get_current_user(request, db)
    except HTTPException:
        return JSONResponse({"error": "not_authenticated"}, status_code=401)

    q = db.query(models.Question).filter(models.Question.id == body.question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    correct = body.selected_option.strip() == q.answer.strip()
    
    # Record Progress
    progress = db.query(models.UserProgress).filter(
        models.UserProgress.user_id == current_user.id,
        models.UserProgress.subject == q.subject,
        models.UserProgress.grade == q.grade,
        models.UserProgress.bloque == q.bloque,
        models.UserProgress.contenido == q.contenido
    ).first()

    if not progress:
        progress = models.UserProgress(
            user_id=current_user.id,
            subject=q.subject,
            grade=q.grade,
            bloque=q.bloque,
            contenido=q.contenido,
            attempts=0,
            successes=0
        )
        db.add(progress)

    progress.attempts += 1
    if correct:
        progress.successes += 1
    progress.last_attempt = datetime.utcnow()
    db.commit()

    return {"correct": correct, "answer": q.answer}


@app.get("/stats/mastery")
async def get_user_mastery(
    request: Request,
    subject: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Returns a summary of topics where the user struggles (success rate < 70%)."""
    try:
        current_user = await get_current_user(request, db)
    except HTTPException:
        return JSONResponse({"error": "not_authenticated"}, status_code=401)

    q = db.query(models.UserProgress).filter(models.UserProgress.user_id == current_user.id)
    if subject:
        q = q.filter(func.lower(models.UserProgress.subject) == subject.lower())
    
    # Get all progress records
    progress_records = q.all()
    
    # Sort by success rate to find weaknesses
    stats = []
    for p in progress_records:
        rate = (p.successes / p.attempts) if p.attempts > 0 else 0
        stats.append({
            "subject": p.subject,
            "grade": p.grade,
            "bloque": p.bloque,
            "contenido": p.contenido,
            "attempts": p.attempts,
            "successes": p.successes,
            "rate": round(rate * 100, 1)
        })
    
    # Sort by rate (worst first)
    stats.sort(key=lambda x: x["rate"])
    
    return {"stats": stats[:5]} # Return top 5 weaknesses


@app.post("/admin/questions")
async def import_questions(
    request: Request,
    db: Session = Depends(get_db),
):
    """Admin-only bulk import of questions from a JSON list."""
    try:
        current_user = await get_current_user(request, db)
    except HTTPException:
        return JSONResponse({"error": "not_authenticated"}, status_code=401)
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")

    data = await request.json()
    questions_data = data if isinstance(data, list) else data.get("questions", [])
    created = 0
    for item in questions_data:
        q = models.Question(
            subject=item["subject"],
            grade=item.get("grade"),
            bloque=item.get("bloque"),
            contenido=item.get("contenido"),
            question=item["question"],
            options=json.dumps(item["options"], ensure_ascii=False),
            answer=item["answer"],
        )
        db.add(q)
        created += 1
    db.commit()
    return {"created": created}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
