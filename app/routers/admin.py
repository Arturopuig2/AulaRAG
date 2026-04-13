import io
import csv
import json
import os
import re
import shutil
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_

from ..database import get_db
from ..models import User, Question, Explanation
from ..auth import get_current_user  # re-use existing auth helper

router = APIRouter(prefix="/admin", tags=["admin"])

# Go up 3 levels from app/routers/admin.py to get to the root
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
templates = Jinja2Templates(directory=os.path.join(ROOT_DIR, "templates"))

# ── Helpers ──────────────────────────────────────────────────────────────────

SUBJECT_PREFIXES = {
    "matematicas":       "MAT",
    "lengua":            "LEN",
    "valenciano":        "VAL",
    "ingles":            "ING",
    "competencia_lectora": "CLE",
}

DIFICULTAD_CODES = {
    "basica":   "B",
    "normal":   "N",
    "avanzada": "A",
}

UPLOAD_DIR = os.path.join(ROOT_DIR, "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def _save_upload(file: UploadFile) -> str:
    """Saves an uploaded file to static/uploads and returns the relative URL."""
    if not file or not file.filename:
        return ""
    
    ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid.uuid4()}{ext}"
    target_path = os.path.join(UPLOAD_DIR, unique_name)
    
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return f"/static/uploads/{unique_name}"


def _generate_identifier(prefix: str, subject: str, grade: int, dificultad: str, db: Session) -> str:
    """Auto-generate a unique identifier like PMAT1N0001."""
    subj_code = SUBJECT_PREFIXES.get(subject, "GEN")
    diff_code  = DIFICULTAD_CODES.get(dificultad, "N")
    base = f"{prefix}{subj_code}{grade or 0}{diff_code}"
    # Find the highest existing sequential number for this prefix
    existing = db.query(Question.identifier if prefix == "P" else Explanation.identifier)\
                 .filter((Question.identifier if prefix == "P" else Explanation.identifier).like(f"{base}%"))\
                 .all()
    numbers = []
    for (val,) in existing:
        if val:
            m = re.search(r'(\d+)$', val)
            if m:
                numbers.append(int(m.group(1)))
    next_n = (max(numbers) + 1) if numbers else 1
    return f"{base}{next_n:04d}"

@router.post("/verify-toggle")
async def verify_toggle(request: Request, db: Session = Depends(get_db)):
    """Toggles the 'is_verified' status for a question or explanation."""
    try:
        user = await require_admin(request, db)
        data = await request.json()
        item_id = data.get("id")
        is_verified = data.get("is_verified")
        item_type = data.get("type", "question") # "question" or "explanation"
        
        model_class = Question if item_type == "question" else Explanation
        item = db.query(model_class).filter(model_class.id == item_id).first()
        
        if not item:
            return JSONResponse({"error": f"{item_type} {item_id} not found"}, status_code=404)
            
        item.is_verified = bool(is_verified)
        db.commit()
        print(f"[ADMIN_LOG] {item_type} {item_id} verification changed to {item.is_verified} by {user.email}")
        return {"ok": True, "id": item_id, "verified": item.is_verified}
    except Exception as e:
        print(f"[ADMIN_ERROR] Verify toggle failed: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.post("/status-toggle-final")
async def status_toggle_final(request: Request, db: Session = Depends(get_db)):
    """Absolute backup endpoint for status toggling."""
    try:
        # Check admin within the function for better error reporting
        user = await get_current_user(request, db)
        if not user or not user.is_admin:
            return JSONResponse({"error": "Admin permission required"}, status_code=403)
            
        data = await request.json()
        qid = data.get("id")
        is_active = data.get("is_active")
        
        q = db.query(Question).filter(Question.id == qid).first()
        if not q:
            return JSONResponse({"error": f"Question {qid} not found in DB"}, status_code=404)
            
        q.is_active = bool(is_active)
        db.commit()
        print(f"[ADMIN_LOG] Question {qid} status changed to {q.is_active} by {user.email}")
        return {"ok": True, "id": qid, "active": q.is_active}
    except Exception as e:
        print(f"[ADMIN_ERROR] Status toggle failed: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

async def require_admin(request: Request, db: Session = Depends(get_db)) -> User:
    try:
        user = await get_current_user(request, db)
    except Exception as e:
        print(f"[AUTH_DEBUG] Usuario no autenticado: {str(e)}")
        raise HTTPException(status_code=401, detail="No autenticado")

    if not user.is_admin:
        print(f"[AUTH_DEBUG] Usuario {user.email} no es admin")
        raise HTTPException(status_code=403, detail="Acceso solo para administradores")
    return user


# ── Pages ─────────────────────────────────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
async def admin_panel(request: Request, db: Session = Depends(get_db)):
    # Check auth manually so we can return a proper redirect response
    try:
        user = await get_current_user(request, db)
    except HTTPException:
        return RedirectResponse(url="/login?next=/admin", status_code=302)
    if not user.is_admin:
        return HTMLResponse("<h1>403 — Sin permiso de administrador</h1>", status_code=403)
    return templates.TemplateResponse("admin.html", {"request": request, "user": user})


# ── Questions API ─────────────────────────────────────────────────────────────

@router.get("/questions")
async def list_questions(
    request: Request,
    subject: Optional[str] = None,
    grade: Optional[int] = None,
    bloque: Optional[str] = None,
    contenido: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    db: Session = Depends(get_db),
):
    await require_admin(request, db)
    q = db.query(Question)
    if subject:
        q = q.filter(Question.subject == subject)
    if grade:
        q = q.filter(Question.grade == grade)
    if bloque:
        q = q.filter(Question.bloque == bloque)
    if contenido:
        q = q.filter(Question.contenido == contenido)
    if search:
        q = q.filter(or_(
            Question.question.ilike(f"%{search}%"),
            Question.identifier.ilike(f"%{search}%"),
        ))
    total = q.count()
    items = q.order_by(Question.created_at.desc()).offset((page - 1) * 20).limit(20).all()
    return {
        "total": total,
        "page": page,
        "items": [_question_to_dict(item) for item in items],
    }


@router.get("/questions/{qid}")
async def get_question(qid: int, request: Request, db: Session = Depends(get_db)):
    await require_admin(request, db)
    q = db.query(Question).filter(Question.id == qid).first()
    if not q:
        raise HTTPException(404, "Pregunta no encontrada")
    return _question_to_dict(q)


@router.post("/questions")
async def create_question(
    request: Request,
    subject: str = Form(...),
    grade: int = Form(...),
    bloque: str = Form(""),
    contenido: str = Form(""),
    dificultad: str = Form("normal"),
    question_type: str = Form("seleccion"),
    question: str = Form(...),
    options: str = Form("[]"),        # JSON string
    answer: str = Form(...),
    explanation: str = Form(""),
    feedback_correct: str = Form(""),
    feedback_incorrect: str = Form(""),
    visual_url: str = Form(""),
    audio_url: str = Form(""),
    visual_file: Optional[UploadFile] = File(None),
    audio_file: Optional[UploadFile] = File(None),
    source: str = Form("manual"),
    identifier: str = Form(""),       # If empty, auto-generate
    db: Session = Depends(get_db),
):
    user = await require_admin(request, db)

    if not identifier:
        identifier = _generate_identifier("P", subject, grade, dificultad, db)

    # Handle file uploads
    uploaded_visual = await _save_upload(visual_file)
    uploaded_audio  = await _save_upload(audio_file)
    
    final_visual = uploaded_visual or visual_url
    final_audio  = uploaded_audio  or audio_url

    # Validate options JSON
    try:
        options_list = json.loads(options) if options else []
    except Exception:
        options_list = []

    new_q = Question(
        identifier=identifier,
        subject=subject,
        grade=grade,
        bloque=bloque or None,
        contenido=contenido or None,
        dificultad=dificultad,
        question_type=question_type,
        question=question,
        options=json.dumps(options_list, ensure_ascii=False),
        answer=answer,
        explanation=explanation or None,
        feedback_correct=feedback_correct or None,
        feedback_incorrect=feedback_incorrect or None,
        visual_url=final_visual or None,
        audio_url=final_audio or None,
        source=source,
        is_active=True,
        created_by=user.id,
    )
    db.add(new_q)
    db.commit()
    db.refresh(new_q)
    return _question_to_dict(new_q)


@router.put("/questions/{qid}")
async def update_question(
    qid: int,
    request: Request,
    subject: str = Form(...),
    grade: int = Form(...),
    bloque: str = Form(""),
    contenido: str = Form(""),
    dificultad: str = Form("normal"),
    question_type: str = Form("seleccion"),
    question: str = Form(...),
    options: str = Form("[]"),
    answer: str = Form(...),
    explanation: str = Form(""),
    feedback_correct: str = Form(""),
    feedback_incorrect: str = Form(""),
    visual_url: str = Form(""),
    audio_url: str = Form(""),
    visual_file: Optional[UploadFile] = File(None),
    audio_file: Optional[UploadFile] = File(None),
    identifier: str = Form(""),
    db: Session = Depends(get_db),
):
    await require_admin(request, db)
    q = db.query(Question).filter(Question.id == qid).first()
    if not q:
        raise HTTPException(404, "Pregunta no encontrada")

    try:
        options_list = json.loads(options) if options else []
    except Exception:
        options_list = []

    q.subject = subject
    q.grade = grade
    q.bloque = bloque or None
    q.contenido = contenido or None
    q.dificultad = dificultad
    q.question_type = question_type
    q.question = question
    q.options = json.dumps(options_list, ensure_ascii=False)
    q.answer = answer
    q.explanation = explanation or None
    q.feedback_correct   = feedback_correct   or None
    q.feedback_incorrect = feedback_incorrect or None
    # Handle new file uploads
    uploaded_visual = await _save_upload(visual_file)
    uploaded_audio  = await _save_upload(audio_file)

    q.visual_url = uploaded_visual or visual_url or None
    q.audio_url  = uploaded_audio  or audio_url or None
    if identifier:
        q.identifier = identifier
    q.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(q)
    return _question_to_dict(q)


@router.delete("/questions/{qid}")
async def delete_question(qid: int, request: Request, db: Session = Depends(get_db)):
    await require_admin(request, db)
    q = db.query(Question).filter(Question.id == qid).first()
    if not q:
        raise HTTPException(404, "Pregunta no encontrada")
    db.delete(q) # Admin delete is permanent for now, or we can use another field if we want two levels
    db.commit()
    return {"ok": True}


# Status update handled in main.py


# ── Explanations API ──────────────────────────────────────────────────────────

@router.get("/explanations")
async def list_explanations(
    request: Request,
    subject: Optional[str] = None,
    grade: Optional[int] = None,
    bloque: Optional[str] = None,
    contenido: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    db: Session = Depends(get_db),
):
    await require_admin(request, db)
    q = db.query(Explanation).filter(Explanation.is_active == True)
    if subject:
        q = q.filter(Explanation.subject == subject)
    if grade:
        q = q.filter(Explanation.grade == grade)
    if bloque:
        q = q.filter(Explanation.bloque == bloque)
    if contenido:
        q = q.filter(Explanation.contenido == contenido)
    if search:
        q = q.filter(or_(
            Explanation.text.ilike(f"%{search}%"),
            Explanation.identifier.ilike(f"%{search}%"),
        ))
    total = q.count()
    items = q.order_by(Explanation.created_at.desc()).offset((page - 1) * 20).limit(20).all()
    return {"total": total, "page": page, "items": [_explanation_to_dict(i) for i in items]}


@router.get("/explanations/{eid}")
async def get_explanation(eid: int, request: Request, db: Session = Depends(get_db)):
    await require_admin(request, db)
    e = db.query(Explanation).filter(Explanation.id == eid).first()
    if not e:
        raise HTTPException(404, "Explicación no encontrada")
    return _explanation_to_dict(e)


@router.post("/explanations")
async def create_explanation(
    request: Request,
    subject: str = Form(...),
    grade: int = Form(...),
    bloque: str = Form(""),
    contenido: str = Form(""),
    dificultad: str = Form("normal"),
    text: str = Form(...),
    steps: str = Form("[]"),
    easier_version: str = Form(""),
    examples: str = Form("[]"),
    audio_url: str = Form(""),
    video_url: str = Form(""),
    visual_url: str = Form(""),
    audio_file: Optional[UploadFile] = File(None),
    video_file: Optional[UploadFile] = File(None),
    visual_file: Optional[UploadFile] = File(None),
    source: str = Form("manual"),
    identifier: str = Form(""),
    db: Session = Depends(get_db),
):
    user = await require_admin(request, db)
    if not identifier:
        # Use Explanation model for ID generation
        subj_code = SUBJECT_PREFIXES.get(subject, "GEN")
        diff_code  = DIFICULTAD_CODES.get(dificultad, "N")
        base = f"E{subj_code}{grade or 0}{diff_code}"
        existing = db.query(Explanation.identifier).filter(Explanation.identifier.like(f"{base}%")).all()
        numbers = []
        for (val,) in existing:
            if val:
                m = re.search(r'(\d+)$', val)
                if m:
                    numbers.append(int(m.group(1)))
        next_n = (max(numbers) + 1) if numbers else 1
        identifier = f"{base}{next_n:04d}"

    # Handle file uploads
    uploaded_audio = await _save_upload(audio_file)
    uploaded_video = await _save_upload(video_file)
    uploaded_visual = await _save_upload(visual_file)

    new_e = Explanation(
        identifier=identifier,
        subject=subject,
        grade=grade,
        bloque=bloque or None,
        contenido=contenido or None,
        dificultad=dificultad,
        text=text,
        steps=steps if steps != "[]" else None,
        easier_version=easier_version or None,
        examples=examples if examples != "[]" else None,
        audio_url=uploaded_audio or audio_url or None,
        video_url=uploaded_video or video_url or None,
        visual_url=uploaded_visual or visual_url or None,
        source=source,
        is_active=True,
        created_by=user.id,
    )
    db.add(new_e)
    db.commit()
    db.refresh(new_e)
    return _explanation_to_dict(new_e)


@router.put("/explanations/{eid}")
async def update_explanation(
    eid: int,
    request: Request,
    subject: str = Form(...),
    grade: int = Form(...),
    bloque: str = Form(""),
    contenido: str = Form(""),
    dificultad: str = Form("normal"),
    text: str = Form(...),
    steps: str = Form("[]"),
    easier_version: str = Form(""),
    examples: str = Form("[]"),
    audio_url: str = Form(""),
    video_url: str = Form(""),
    visual_url: str = Form(""),
    audio_file: Optional[UploadFile] = File(None),
    video_file: Optional[UploadFile] = File(None),
    visual_file: Optional[UploadFile] = File(None),
    identifier: str = Form(""),
    db: Session = Depends(get_db),
):
    await require_admin(request, db)
    e = db.query(Explanation).filter(Explanation.id == eid).first()
    if not e:
        raise HTTPException(404, "Explicación no encontrada")

    e.subject = subject
    e.grade = grade
    e.bloque = bloque or None
    e.contenido = contenido or None
    e.dificultad = dificultad
    e.text = text
    e.steps = steps if steps != "[]" else None
    e.easier_version = easier_version or None
    e.examples = examples if examples != "[]" else None
    # Handle new file uploads
    uploaded_audio = await _save_upload(audio_file)
    uploaded_video = await _save_upload(video_file)
    uploaded_visual = await _save_upload(visual_file)

    e.audio_url = uploaded_audio or audio_url or None
    e.video_url = uploaded_video or video_url or None
    e.visual_url = uploaded_visual or visual_url or None
    if identifier:
        e.identifier = identifier
    e.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(e)
    return _explanation_to_dict(e)


@router.delete("/explanations/{eid}")
async def delete_explanation(eid: int, request: Request, db: Session = Depends(get_db)):
    await require_admin(request, db)
    e = db.query(Explanation).filter(Explanation.id == eid).first()
    if not e:
        raise HTTPException(404, "Explicación no encontrada")
    e.is_active = False
    db.commit()
    return {"ok": True}


# ── Import JSON / CSV ─────────────────────────────────────────────────────────

@router.post("/import/questions")
async def import_questions(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Bulk import questions from a JSON or CSV file."""
    user = await require_admin(request, db)
    content = await file.read()

    rows = []
    if file.filename.endswith(".json"):
        try:
            rows = json.loads(content)
        except Exception as e:
            raise HTTPException(400, f"JSON inválido: {e}")
    elif file.filename.endswith(".csv"):
        try:
            reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
            rows = list(reader)
        except Exception as e:
            raise HTTPException(400, f"CSV inválido: {e}")
    else:
        raise HTTPException(400, "Solo se admiten archivos .json o .csv")

    created, skipped = 0, 0
    for row in rows:
        subject    = row.get("subject", "").strip()
        question   = row.get("question", "").strip()
        answer     = row.get("answer", "").strip()
        if not subject or not question or not answer:
            skipped += 1
            continue

        grade_raw  = row.get("grade") or row.get("curso") or 0
        opts_raw   = row.get("options") or row.get("opciones") or "[]"
        if isinstance(opts_raw, str):
            try:
                opts_list = json.loads(opts_raw)
            except Exception:
                opts_list = [o.strip() for o in opts_raw.split("|") if o.strip()]
        else:
            opts_list = opts_raw

        dificultad = row.get("dificultad", "normal").strip() or "normal"
        identifier = row.get("identifier") or row.get("id") or ""
        if not identifier:
            identifier = _generate_identifier("P", subject, int(grade_raw or 0), dificultad, db)

        # Skip duplicates by identifier
        if db.query(Question).filter(Question.identifier == identifier).first():
            skipped += 1
            continue

        new_q = Question(
            identifier=identifier,
            subject=subject,
            grade=int(grade_raw) if grade_raw else None,
            bloque=row.get("bloque", "") or None,
            contenido=row.get("contenido", "") or None,
            dificultad=dificultad,
            question_type=row.get("question_type", "seleccion") or "seleccion",
            question=question,
            options=json.dumps(opts_list, ensure_ascii=False),
            answer=answer,
            explanation=row.get("explanation") or row.get("explicacion") or None,
            source=row.get("source", "ia_csv") or "ia_csv",
            is_active=True,
            created_by=user.id,
        )
        db.add(new_q)
        created += 1

    db.commit()
    return {"created": created, "skipped": skipped, "total_in_file": len(rows)}


# ── AI Generation (Preview) ───────────────────────────────────────────────────

@router.post("/generate/question")
async def generate_question_with_ai(
    request: Request,
    subject: str = Form(...),
    grade: int = Form(...),
    bloque: str = Form(""),
    contenido: str = Form(""),
    dificultad: str = Form("normal"),
    question_type: str = Form("seleccion"),
    source: str = Form("ia_pdf"),     # ia_pdf | ia_csv
    db: Session = Depends(get_db),
):
    """Ask Gemini to generate a question. Returns a preview (not saved yet)."""
    await require_admin(request, db)

    try:
        from ..rag_engine import client, MODEL_NAME, existing_files_cache
        from google.genai import types

        subject_names = {
            "matematicas": "Matemáticas", "lengua": "Lengua Española",
            "valenciano": "Valenciano", "ingles": "Inglés",
            "competencia_lectora": "Competencia Lectora",
        }

        type_instructions = {
            "seleccion":       "3 opciones de selección múltiple (solo una correcta)",
            "verdadero_falso": "de Verdadero o Falso",
            "pasos":           "de resolución por pasos",
        }

        prompt = (
            f"Eres un experto en educación primaria española. Genera UNA pregunta de {type_instructions.get(question_type, 'selección múltiple')} "
            f"para {subject_names.get(subject, subject)}, curso {grade}º de primaria"
            + (f", tema: {bloque}" if bloque else "")
            + (f", contenido: {contenido}" if contenido else "")
            + f", nivel de dificultad: {dificultad}.\n\n"
            "Responde EXCLUSIVAMENTE con un JSON válido con esta estructura exacta:\n"
            "{\n"
            '  "question": "Enunciado completo",\n'
            '  "options": ["Opción A", "Opción B", "Opción C"],\n'
            '  "answer": "Opción A",\n'
            '  "explanation": "Explicación pedagógica breve de la respuesta correcta"\n'
            "}\n"
            "Para preguntas de Verdadero/Falso, options debe ser [\"Verdadero\", \"Falso\"].\n"
            "Para preguntas de resolución por pasos, options puede estar vacío [].\n"
            "No añadas texto antes ni después del JSON."
        )

        # Attach relevant PDF files if available (ia_pdf source)
        contents = [types.Part(text=prompt)]
        if source == "ia_pdf":
            for name, f in existing_files_cache.items():
                if subject.lower() in name.lower():
                    contents.insert(0, types.Part(file_data=types.FileData(file_uri=f.uri, mime_type="application/pdf")))
                    break  # Just attach one relevant PDF

        response = await client.aio.models.generate_content(
            model=MODEL_NAME,
            contents=[types.Content(role="user", parts=contents)],
        )

        raw = response.text.strip()
        # Strip markdown code fence if present
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        data = json.loads(raw)

        return {
            "question":    data.get("question", ""),
            "options":     data.get("options", []),
            "answer":      data.get("answer", ""),
            "explanation": data.get("explanation", ""),
        }

    except Exception as e:
        raise HTTPException(500, f"Error generando con IA: {e}")


# ── Serializers ───────────────────────────────────────────────────────────────

def _question_to_dict(q: Question) -> dict:
    return {
        "id":            q.id,
        "identifier":    q.identifier,
        "subject":       q.subject,
        "grade":         q.grade,
        "bloque":        q.bloque,
        "contenido":     q.contenido,
        "dificultad":    q.dificultad,
        "question_type": q.question_type,
        "question":      q.question,
        "options":       json.loads(q.options) if q.options else [],
        "answer":        q.answer,
        "explanation":       q.explanation,
        "feedback_correct":  q.feedback_correct,
        "feedback_incorrect": q.feedback_incorrect,
        "visual_url":    q.visual_url,
        "audio_url":     q.audio_url,
        "source":        q.source,
        "is_active":     q.is_active,
        "is_verified":   q.is_verified,
        "created_at":    q.created_at.isoformat() if q.created_at else None,
    }


def _explanation_to_dict(e: Explanation) -> dict:
    return {
        "id":              e.id,
        "identifier":      e.identifier,
        "subject":         e.subject,
        "grade":           e.grade,
        "bloque":          e.bloque,
        "contenido":       e.contenido,
        "dificultad":      e.dificultad,
        "text":            e.text,
        "steps":           json.loads(e.steps) if e.steps else [],
        "easier_version":  e.easier_version,
        "examples":        json.loads(e.examples) if e.examples else [],
        "audio_url":       e.audio_url,
        "video_url":       e.video_url,
        "visual_url":      e.visual_url,
        "source":          e.source,
        "is_active":       e.is_active,
        "is_verified":     e.is_verified,
        "created_at":      e.created_at.isoformat() if e.created_at else None,
    }
