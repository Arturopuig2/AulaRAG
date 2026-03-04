import json
import os
import re

from fastapi import Depends, FastAPI, Form, HTTPException, Request, UploadFile, File, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
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
        "lengua":      "lengua/temario_lengua.json",
        "matematicas": "matematicas/temario_matematicas.txt",
        "valenciano":  "valenciano/temario_valenciano.json",
        "ingles":      "ingles/temario_ingles.json",
    }

    relative_path = SUBJECT_FILES.get(subject.lower())
    if not relative_path:
        raise HTTPException(status_code=404, detail=f"Temario not found for subject: '{subject}'")

    file_path = os.path.join(os.path.dirname(__file__), "..", "data", "source_files", relative_path)
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
        response_text = await get_gemini_response(message, subject, course_level, str(current_user.email), reset_history)
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

    source_dir = os.path.join(os.path.dirname(__file__), "..", "data", "source_files", subject)
    os.makedirs(source_dir, exist_ok=True)
    file_path = os.path.join(source_dir, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    success = upload_new_file_to_gemini(file_path, subject)
    if success:
        return {"filename": file.filename, "status": "Successfully uploaded and indexed by Gemini"}
    else:
        return {"error": "Failed to index file in Gemini API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
