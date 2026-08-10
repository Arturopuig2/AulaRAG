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
from ..models import User, Explanation
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
@router.get("/exercises", response_class=HTMLResponse)
async def admin_panel(request: Request, db: Session = Depends(get_db)):
    # Check auth manually so we can return a proper redirect response
    try:
        user = await get_current_user(request, db)
    except HTTPException:
        return RedirectResponse(url="/login?next=/admin", status_code=302)
    if not user.is_admin:
        return HTMLResponse("<h1>403 — Sin permiso de administrador</h1>", status_code=403)
    return templates.TemplateResponse("admin_exercises.html", {"request": request, "user": user})


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


# ── Image Gallery & Tagging API ───────────────────────────────────────────────

@router.get("/api/gallery")
async def list_image_gallery(query: Optional[str] = None):
    """Scans and returns all available image assets for image tagging."""
    images = []
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    scan_folders = [
        os.path.join(base_dir, "static", "assets", "extracted"),
        os.path.join(base_dir, "static", "assets", "extracted2"),
        os.path.join(base_dir, "static", "uploads", "extracted_images"),
    ]
    
    valid_exts = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
    
    for folder in scan_folders:
        if not os.path.exists(folder):
            continue
        rel_base = os.path.relpath(folder, base_dir)
        for root, _, files in os.walk(folder):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in valid_exts:
                    full_path = os.path.join(root, file)
                    rel_url = "/" + os.path.relpath(full_path, base_dir).replace("\\", "/")
                    
                    if query:
                        q_lower = query.lower()
                        if q_lower not in file.lower() and q_lower not in rel_url.lower():
                            continue
                    
                    images.append({
                        "url": rel_url,
                        "name": file,
                        "folder": os.path.basename(os.path.dirname(full_path))
                    })
                    if len(images) >= 150: # Cap for UI performance
                        break
            if len(images) >= 150:
                break
                
    return {"total": len(images), "images": images}


# ── JSON API for Exercises & Explanations ──────────────────────────────────────

@router.post("/api/upload-image")
async def api_upload_image(file: UploadFile = File(...)):
    """Uploads a local image file and returns its static URL."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "El archivo debe ser una imagen (JPG, PNG, GIF, WEBP).")

    ext = os.path.splitext(file.filename)[1].lower() or ".png"
    filename = f"{uuid.uuid4()}{ext}"
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    file_path = os.path.join(uploads_dir, filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    return {"url": f"/static/uploads/{filename}", "filename": filename}


@router.post("/api/upload-video")
async def api_upload_video(file: UploadFile = File(...)):
    """Uploads a local video file (MP4, WEBM, MOV, AVI) and returns its static URL."""
    valid_exts = {".mp4", ".webm", ".mov", ".avi", ".mkv", ".ogv"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in valid_exts and not file.content_type.startswith("video/"):
        raise HTTPException(400, "El archivo debe ser un vídeo (MP4, WEBM, MOV, AVI).")

    filename = f"{uuid.uuid4()}{ext or '.mp4'}"
    uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    file_path = os.path.join(uploads_dir, filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    return {"url": f"/static/uploads/{filename}", "filename": filename}


@router.get("/api/search-web-images")
async def api_search_web_images(query: str):
    """Searches educational web images using Wikimedia Commons API & Unsplash Educational API."""
    if not query or len(query.strip()) < 2:
        return {"images": []}

    results = []

    # 1. Wikimedia Commons API Search
    try:
        import urllib.request, json as json_mod, urllib.parse
        encoded_q = urllib.parse.quote(query)
        wiki_url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6&gsrsearch={encoded_q}&gsrlimit=12&prop=imageinfo&iiprop=url|mime|size&format=json"
        
        req = urllib.request.Request(wiki_url, headers={'User-Agent': 'AulaRAG-Educational-App/1.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json_mod.loads(resp.read().decode('utf-8'))
            pages = data.get('query', {}).get('pages', {})
            for page_id, page in pages.items():
                imageinfo = page.get('imageinfo', [])
                if imageinfo:
                    img_url = imageinfo[0].get('url')
                    title = page.get('title', 'Imagen Web').replace('File:', '')
                    if img_url and any(img_url.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.svg', '.webp']):
                        results.append({
                            "title": title,
                            "url": img_url,
                            "source": "Wikimedia"
                        })
    except Exception as e:
        print("[WEB_IMAGE_SEARCH_ERROR] Wikimedia:", e)

    # 2. Open Educational Unsplash Direct Search Fallback
    try:
        encoded_q = urllib.parse.quote(query)
        # Unsplash Source / Public Direct Query
        unsplash_urls = [
            {"title": f"{query.capitalize()} 1", "url": f"https://source.unsplash.com/400x300/?{encoded_q}", "source": "Unsplash"},
            {"title": f"{query.capitalize()} 2", "url": f"https://source.unsplash.com/400x300/?{encoded_q},education", "source": "Unsplash"},
            {"title": f"{query.capitalize()} 3", "url": f"https://source.unsplash.com/400x300/?{encoded_q},school", "source": "Unsplash"}
        ]
        results.extend(unsplash_urls)
    except Exception as e:
        print("[WEB_IMAGE_SEARCH_ERROR] Unsplash:", e)

    return {"images": results}


@router.get("/api/options")
async def get_filter_options(subject: Optional[str] = None, grade: Optional[int] = None, bloque: Optional[str] = None, db: Session = Depends(get_db)):
    """Returns unique Bloques and Contenidos for dynamic dropdown filtering."""
    q = db.query(Explanation).filter(Explanation.is_active == True)
    if subject:
        q = q.filter(Explanation.subject == subject)
    if grade:
        q = q.filter(Explanation.grade == grade)
    if bloque:
        q = q.filter(Explanation.bloque == bloque)
    
    items = q.all()
    bloques = sorted(list({i.bloque for i in items if i.bloque}))
    contenidos = sorted(list({i.contenido for i in items if i.contenido}))
    return {"bloques": bloques, "contenidos": contenidos}


@router.get("/api/explanations")
async def api_list_explanations(
    subject: Optional[str] = None,
    grade: Optional[int] = None,
    bloque: Optional[str] = None,
    contenido: Optional[str] = None,
    query: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(Explanation).filter(Explanation.is_active == True)
    if subject:
        q = q.filter(Explanation.subject == subject)
    if grade:
        q = q.filter(Explanation.grade == grade)
    if bloque:
        q = q.filter(Explanation.bloque.ilike(f"%{bloque}%"))
    if contenido:
        q = q.filter(Explanation.contenido.ilike(f"%{contenido}%"))
    if query:
        q = q.filter(or_(
            Explanation.contenido.ilike(f"%{query}%"),
            Explanation.bloque.ilike(f"%{query}%"),
            Explanation.text.ilike(f"%{query}%")
        ))
    items = q.order_by(Explanation.id.desc()).limit(150).all()
    return {"explanations": [_explanation_to_dict(i) for i in items]}


@router.post("/api/explanations")
async def api_create_explanation(payload: dict, db: Session = Depends(get_db)):
    subject = payload.get("subject", "matematicas")
    grade = int(payload.get("grade", 1))
    bloque = payload.get("bloque", "")
    contenido = payload.get("contenido", "")
    text = payload.get("text", "")
    easier_version = payload.get("easier_version", "")
    examples = payload.get("examples", [])
    visual_url = payload.get("visual_url", "")
    video_url = payload.get("video_url", "")
    easier_visual_url = payload.get("easier_visual_url", "")
    examples_visual_url = payload.get("examples_visual_url", "")
    
    if not contenido or not text:
        raise HTTPException(400, "Contenido y texto son requeridos")
        
    e = Explanation(
        subject=subject,
        grade=grade,
        bloque=bloque or None,
        contenido=contenido or None,
        text=text,
        easier_version=easier_version or None,
        examples=json.dumps(examples, ensure_ascii=False) if isinstance(examples, list) else (examples or None),
        visual_url=visual_url or None,
        video_url=video_url or None,
        easier_visual_url=easier_visual_url or None,
        examples_visual_url=examples_visual_url or None,
        is_active=True,
        is_verified=True
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return _explanation_to_dict(e)


@router.put("/api/explanations/{eid}")
async def api_update_explanation(eid: int, payload: dict, db: Session = Depends(get_db)):
    e = db.query(Explanation).filter(Explanation.id == eid).first()
    if not e:
        raise HTTPException(404, "Explicación no encontrada")
        
    if "subject" in payload: e.subject = payload["subject"]
    if "grade" in payload: e.grade = int(payload["grade"])
    if "bloque" in payload: e.bloque = payload["bloque"] or None
    if "contenido" in payload: e.contenido = payload["contenido"] or None
    if "text" in payload: e.text = payload["text"]
    if "easier_version" in payload: e.easier_version = payload["easier_version"] or None
    if "examples" in payload: 
        ex_val = payload["examples"]
        e.examples = json.dumps(ex_val, ensure_ascii=False) if isinstance(ex_val, list) else (ex_val or None)
    if "visual_url" in payload: e.visual_url = payload["visual_url"] or None
    if "video_url" in payload: e.video_url = payload["video_url"] or None
    if "easier_visual_url" in payload: e.easier_visual_url = payload["easier_visual_url"] or None
    if "examples_visual_url" in payload: e.examples_visual_url = payload["examples_visual_url"] or None
    
    e.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(e)
    return _explanation_to_dict(e)


@router.delete("/api/explanations/{eid}")
async def api_delete_explanation(eid: int, db: Session = Depends(get_db)):
    e = db.query(Explanation).filter(Explanation.id == eid).first()
    if not e:
        raise HTTPException(404, "Explicación no encontrada")
    e.is_active = False
    db.commit()
    return {"ok": True}


# ── AI Generation (Theory Preview) ─────────────────────────────────────────────

@router.post("/api/ai/generate-section")
async def generate_explanation_section_ai(payload: dict):
    """Generates a specific section (text, easier_version, or examples) using Gemini AI."""
    from ..rag_engine import get_client, get_model_name
    from google.genai import types

    client = get_client()
    model_name = get_model_name()
    if not client:
        raise HTTPException(500, "GEMINI_API_KEY no configurada")

    subject = payload.get("subject", "matematicas")
    grade = int(payload.get("grade", 1))
    bloque = payload.get("bloque", "")
    contenido = payload.get("contenido", "")
    section = payload.get("section", "text")

    if not contenido:
        raise HTTPException(400, "Debes indicar el contenido/tema antes de generar.")

    lang_instr = "español"
    if subject == "valenciano":
        lang_instr = "valencià normatiu (AVL)"
    elif subject == "ingles":
        lang_instr = "forma BILINGÜE combinando INGLÉS Y ESPAÑOL (para alumnos muy pequeños de Educación Primaria con nivel inicial). Muestra cada término o frase en inglés acompañado de su traducción y explicación sencilla en español."

    # Determinar ruta base del directorio de prompts
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    prompts_dir = os.path.join(base_dir, "prompts")

    def read_prompt_file(filename: str, default_text: str) -> str:
        filepath = os.path.join(prompts_dir, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading prompt file {filename}: {e}")
        return default_text

    bloque_str = f" (Bloque: {bloque})" if bloque else ""

    if section == "text":
        if subject == "ingles":
            default_tpl = (
                "Eres un maestro de Inglés de Educación Primaria en España. Genera la EXPLICACIÓN TEÓRICA perfecta "
                "para el tema '{contenido}' de {grade}º de Primaria{bloque_str}.\n\n"
                "Sigue ESTRICTAMENTE este formato Markdown, sustituyendo los marcadores entre corchetes:\n\n"
                "## [Título en Inglés / Título en Español]\n\n"
                "[1 o 2 frases cortas de introducción al tema, en español]\n\n"
                "---\n\n"
                "### [Subtítulo de la primera regla o concepto]\n\n"
                "* **[ESTRUCTURA O PREGUNTA PRINCIPAL EN INGLÉS]** ([Traducción al español])\n"
                "  - **[Palabra clave 1]:** [Explicación en 3-5 palabras]\n"
                "  - **[Palabra clave 2]:** [Explicación en 3-5 palabras]\n\n"
                "---\n\n"
                "### [Subtítulo de la segunda regla o concepto]\n\n"
                "* **[ESTRUCTURA O RESPUESTA EN INGLÉS]** ([Traducción al español])\n"
                "  - **[Palabra clave 1]:** [Explicación en 3-5 palabras]\n"
                "  - **[Palabra clave 2]:** [Explicación en 3-5 palabras]\n\n"
                "---\n\n"
                "### ¡Ejemplo en la vida real!\n\n"
                "> **[Nombre Personaje 1]:** [Frase corta en inglés] ([Traducción al español])\n"
                "> **[Nombre Personaje 2]:** [Frase corta en inglés] ([Traducción al español])\n\n"
                "REGLAS IMPORTANTES:\n"
                "- Usa siempre inglés para las estructuras y palabras clave; el español solo para traducciones y explicaciones.\n"
                "- Lenguaje muy sencillo, pensado para niños de primaria.\n"
                "- PROHIBIDO añadir ejercicios, tests o cuestionarios.\n"
                "- Responde EXCLUSIVAMENTE con el texto en markdown. Sin bloques de código ni JSON."
            )
            template = read_prompt_file("ingles_teoria.txt", default_tpl)
            prompt = template.format(contenido=contenido, grade=grade, bloque_str=bloque_str)
        else:
            default_tpl = (
                "Eres un maestro pedagogo de Educación Primaria experto en España. Genera en {lang_instr} la EXPLICACIÓN TEÓRICA perfecta para el tema '{contenido}' "
                "del curso {grade}º de Primaria{bloque_str}.\n"
                "Estructúrala con títulos claros en Markdown (Concepto Didáctico, Reglas y Explicación, Ejemplos Prácticos, Resumen).\n"
                "REGLAS OBLIGATORIAS DE ESTILO:\n"
                "- Usa un tono 100% FORMAL, CLARO y RIGUROSO, imitando exactamente el estilo de un LIBRO DE TEXTO escolar oficial. Ten en cuenta que estos textos son leídos por los PADRES de los alumnos.\n"
                "- PROHIBIDO TOTALMENTE cualquier infantilismo o teatralidad como '¡Hola, pequeños exploradores!', 'partes mágicas', 'corazón de las palabras', '¡Verás qué fácil!', etc.\n"
                "- PROHIBIDO proponer ejercicios, cuestionarios o tests al alumno.\n"
                "Responde EXCLUSIVAMENTE con el texto completo en markdown, sin envolver en JSON ni bloques de código."
            )
            template = read_prompt_file("default_teoria.txt", default_tpl)
            prompt = template.format(lang_instr=lang_instr, contenido=contenido, grade=grade, bloque_str=bloque_str)
    elif section == "easier_version":
        default_tpl = (
            "Eres un maestro pedagogo de Educación Primaria experto en España. Genera en {lang_instr} una VERSIÓN FÁCIL Y ADAPTADA del tema '{contenido}' "
            "para {grade}º de Primaria, enfocada a alumnos con necesidades educativas o dificultades de comprensión.\n"
            "Usa frases muy sencillas, explicaciones intuitivas y lenguaje cercano.\n"
            "Responde EXCLUSIVAMENTE con el texto adaptado en markdown, sin envolver en JSON ni bloques de código."
        )
        template = read_prompt_file("default_easier.txt", default_tpl)
        prompt = template.format(lang_instr=lang_instr, contenido=contenido, grade=grade)
    elif section == "examples":
        default_tpl = (
            "Eres un maestro pedagogo de Educación Primaria experto en España. Genera en {lang_instr} 3 EJEMPLOS PRÁCTICOS DE LA VIDA REAL para el tema '{contenido}' "
            "de {grade}º de Primaria.\n"
            "Responde EXCLUSIVAMENTE con un JSON válido que contenga un array de strings: [\"Ejemplo 1...\", \"Ejemplo 2...\", \"Ejemplo 3...\"]. No añadas texto antes ni después."
        )
        template = read_prompt_file("default_examples.txt", default_tpl)
        prompt = template.format(lang_instr=lang_instr, contenido=contenido, grade=grade)
    else:
        raise HTTPException(400, "Sección no válida")

    try:
        sys_instr = (
            "Eres un redactor de contenidos para un LIBRO DE TEXTO escolar oficial de Educación Primaria. "
            "PROHIBIDO ABSOLUTAMENTE incluir saludos, despedidas, mensajes teatrales o infantilismos "
            "(como '¡Hola, pequeños exploradores!', 'letras cantarinas', '¡Vamos a aprender!', etc.). "
            "Tu respuesta debe ser ÚNICA Y EXCLUSIVAMENTE la lección teórica formal, clara y rigurosa en formato Markdown."
        )
        response = await client.aio.models.generate_content(
            model=model_name,
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
            config=types.GenerateContentConfig(
                system_instruction=sys_instr,
                temperature=0.0
            )
        )

        raw = response.text.strip()
        if section == "examples":
            raw = re.sub(r'^```(?:json)?\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)
            ex_list = json.loads(raw)
            if isinstance(ex_list, list):
                ex_list = [re.sub(r'^•\s*', '', str(item)).strip() for item in ex_list]
            return {"result": ex_list}
        else:
            from ..multi_agent_system import AgenteAuditor
            clean_text = AgenteAuditor.audit_and_clean(raw, subject)
            return {"result": clean_text}

    except Exception as e:
        raise HTTPException(500, f"Error generando la sección {section} con IA: {e}")


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


# ── AI Generation (Theory Preview) ─────────────────────────────────────────────


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
        "easier_visual_url": e.easier_visual_url,
        "examples_visual_url": e.examples_visual_url,
        "source":          e.source,
        "is_active":       e.is_active,
        "is_verified":     e.is_verified,
        "created_at":      e.created_at.isoformat() if e.created_at else None,
    }
