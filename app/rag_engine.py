import json
import os
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types
import random as _random
from .database import SessionLocal
from . import models
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime, timezone

# Load variables from .env file, overriding any system environment variables
load_dotenv(override=True)

# Helper to always fetch a fresh client with current environment variables
def get_client():
    load_dotenv(override=True)
    api_key = os.environ.get("GEMINI_API_KEY", "")
    return genai.Client(api_key=api_key) if api_key else None

client = get_client()

# Model to use - gemini-flash-lite-latest has fast response times and avoids 503 demand spikes
MODEL_NAME = "gemini-flash-lite-latest"

def normalize_text(text):
    import unicodedata
    if not text: return ""
    return "".join(c for c in unicodedata.normalize('NFD', str(text)) if unicodedata.category(c) != 'Mn').lower()

def clean_ai_text(text: str) -> str:
    """Removes segments that only contain punctuation or artifacts like '¡!'."""
    if not text:
        return text
    
    # Fix markdown header collisions like ---### 1. Title into clean double newlines
    text = re.sub(r'---+\s*(#{1,6}\s*)', r'\n\n\1', text)
    text = re.sub(r'(#{1,6}\s*[^\n]+)', r'\n\1\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Remove bracket tags like [INCORRECTE], [CORRECTE], [INCORRECTO], [CORRECTO]
    text = re.sub(r'\[\s*(?:INCORRECTE|CORRECTE|INCORRECTO|CORRECTO)\s*\]', '', text, flags=re.IGNORECASE)

    # Remove specific nonsensical combinations (junk artifacts)
    text = re.sub(r'¡!', '', text)
    text = re.sub(r'!¡', '', text)
    text = re.sub(r'¿\?', '', text)
    text = re.sub(r'\?¿', '', text)

    # Collapse repeating symbols (¡¡ -> ¡, !! -> !, etc.)
    text = re.sub(r'¡{2,}', '¡', text)
    text = re.sub(r'!{2,}', '!', text)
    text = re.sub(r'¿{2,}', '¿', text)
    text = re.sub(r'\?{2,}', '?', text)

    # Remove junk like "! !" or "¡ !" while keeping symbols but no extra spaces between them
    text = re.sub(r'([¡!¿?])\s+([¡!¿?])', r'\1\2', text)

    # REGLA DE ORO DE ESPACIADO: Forzar espacio después de puntuación si no lo hay (ej: "?Sacar" -> "? Sacar")
    text = re.sub(r'([.!?,;:])([a-zA-ZáéíóúÁÉÍÓÚñÑ0-9¿¡])', r'\1 \2', text)
    text = re.sub(r'([!?])([a-zA-ZáéíóúÁÉÍÓÚñÑ0-9¿¡])', r'\1 \2', text)

    # REGLA DE FORMATO: Convertir "texto" o 'texto' en **texto** (negrita) automáticamente
    text = re.sub(r'"([^"]+)"', r'**\1**', text)
    text = re.sub(r"(?<![a-zA-ZáéíóúÁÉÍÓÚñÑ])'([^']+)'(?![a-zA-ZáéíóúÁÉÍÓÚñÑ])", r"**\1**", text)

    # --- FILTRO ANTI-PENSAMIENTO INTERNO ---
    meta_patterns = [
        r'El modelo no pudo encontrar[^.]+\.',
        r'Debo crear una pregunta[^.]+\.',
        r'Voy a generar[^.]+\.',
        r'No hay preguntas verificadas[^.]+\.',
        r'Será el Ejercicio \d+/\d+\.',
        r'PROHIBICIÓN ESTRUCTURAL ABSOLUTA\.?',
        r'Usa negrita \*\* \*\*\.?',
        r'NUNCA uses? comillas\.?',
        r'Obligatorio usar \[[^\]]+\]\.?',
        r'Solo UN ejercicio por turno\.?',
        r'No menciones reglas\.?',
        r'I need to generate[^.]+\.',
        r'Generating exercise[^.]+\.',
        r'The student correctly[^.]+\.',
        r'Paso \d+: Operación\.?',
        r'Options:?'
    ]
    for p in meta_patterns:
        text = re.sub(p, '', text, flags=re.IGNORECASE)

    # Clean up double spaces or triple newlines left by pruning
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.lstrip(" !.,\n")

    # REGLA NEUTRA AUTOMÁTICA
    replacements = {
        r'\b[Cc]ampe[óo]n\b': 'genial',
        r'\b[Cc]ampeona\b': 'genial',
        r'\b[Ll]isto\b': 'brillante',
        r'\b[Ll]ista\b': 'brillante',
        r'\b[Nn]i[ñn]o\b': 'estudiante',
        r'\b[Nn]i[ñn]a\b': 'estudiante'
    }
    for pattern, substitution in replacements.items():
        text = re.sub(pattern, substitution, text)
    
    segments = text.split('---')
    cleaned_segments = []
    for seg in segments:
        s = seg.strip()
        if not s or not re.search(r'[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ]', s):
            continue
        cleaned_segments.append(s)
    
    return '---'.join(cleaned_segments).strip()

FEW_SHOT_EXAMPLES = """
### EJEMPLOS DE ESTILO (AULA) ###

1. EXPLICACIÓN TEÓRICA CON EJEMPLOS:
   USUARIO: "Quiero repasar los sustantivos."
   TUTOR: "¡Genial! Los **sustantivos** son las palabras que usamos para nombrar todo lo que nos rodea: personas, animales, objetos o lugares. 

   Por ejemplo:
   * **Personas**: Sofía, profesor, niña.
   * **Animales**: león, perro, pájaro.
   * **Objetos**: casa, mesa, libro.

   ¿Tienes alguna duda sobre los sustantivos o quieres ver más ejemplos?"
"""

SYSTEM_INSTRUCTION = f"""
Eres 'Aula', un tutor experto de primaria. Tu misión es enseñar TEORÍA y dar EJEMPLOS CLAROS a niños de 6 a 12 años ÚNICAMENTE con los contenidos verificados de la base de datos y los documentos RAG de consulta.

### EL MANDATO SUPREMO:
1. **HERRAMIENTA DE TEORÍA**: Tu objetivo es EXPLICAR CONCEPTOS Y DAR EJEMPLOS. Tienes estrictamente PROHIBIDO proponer ejercicios, cuestionarios, preguntas de examen o tests al alumno.
2. **SOLO BASE DE DATOS Y RAG**: Basate ÚNICAMENTE en la información verificada de los documentos proporcionados.
3. **PROHIBIDO INTERNET**: No busques en internet ni asumas datos externos.

### REGLAS DE TRABAJO:
- **PUNTOS Y APARTE FRECUENTES**: Es OBLIGATORIO usar párrafos muy cortos. Separa cada idea, concepto o grupo de ejemplos con un **punto y aparte** e introduce un salto de línea doble (\n\n) entre ellos. Evita bloques de texto largos o densos.
- **RIGOR ORTOGRÁFICO ABSOLUTO EN EJEMPLOS**: Revisa con total precisión cada ejemplo. La sílaba o letra en negrita (**) DEBE COINCIDIR EXACTAMENTE con la categoría (ej: en la categoría GE resalta la sílaba **ge** como en pro-te-**ge**r, NUNCA resaltes la sílaba equivocada ni clasifiques palabras con J o GI en la regla de GE).
- **ESQUEMAS Y DIAGRAMAS VISUALES**: Para temas con conceptos clasificables o geométricos (ej: tipos de ángulos, partes de la oración, reglas de acentuación, fracciones), genera cuadros o diagramas visuales en Markdown con esquemas claros para reforzar la visión del alumno.
- **FORMATO DE SECCIONES LIMPIO**: Escribe los títulos de cada sección de forma clara y limpia (ej: **1. La regla de la GE** o `### 1. La regla de la GE`). NUNCA pegues guiones con títulos como `---###`. Deja siempre una línea en blanco antes de cada título.
- **FORMATO CLARO**: Usa listas, viñetas y **negrita** para conceptos clave.
- **TONO**: Sé paciente, claro y motivador, pero neutro (no uses 'campeón' o 'niño').

{FEW_SHOT_EXAMPLES}
"""

# Per-subject chat history (preserved when switching subjects)
chat_histories: dict[str, list] = {}  # subject -> list of Content messages
existing_files_cache = {}  # display_name -> genai File object

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CACHE_FILE = os.path.join(DATA_DIR, "gemini_file_cache.json")
CONTEXT_DIR = os.path.join(BASE_DIR, "context")


def load_context_rules(subject: str = None) -> str:
    """Lee reglas_generales.txt y reglas_{subject}.txt de la carpeta context/.
    Ignora líneas vacías y comentarios (empiezan por #).
    Devuelve el bloque de reglas formateado, o cadena vacía si no hay nada."""
    rules_parts = []

    def _read_rules(path: str, label: str):
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            lines = [
                line.strip() for line in f
                if line.strip() and not line.strip().startswith("#")
            ]
        if lines:
            rules_parts.append(f"[{label}]\n" + "\n".join(lines))

    _read_rules(os.path.join(CONTEXT_DIR, "reglas_generales.txt"), "REGLAS GENERALES")
    if subject:
        subject_file = f"reglas_{subject.lower()}.txt"
        _read_rules(os.path.join(CONTEXT_DIR, subject_file), f"REGLAS DE {subject.upper()}")

    if not rules_parts:
        return ""

    block = "\n\n".join(rules_parts)
    print(f"[context] Reglas cargadas para subject='{subject}' ({len(block)} chars)")
    return block


def _load_persistent_cache() -> dict:
    """Loads the cached Gemini file URIs from disk (if available)."""
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  [cache] Could not read cache file: {e}")
        return {}


def _save_persistent_cache(cache: dict):
    """Persists the current cache (display_name -> uri) to disk."""
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"  [cache] Could not write cache file: {e}")


def load_pdf_files_as_parts():
    """Scans the subject folders and uploads any new PDFs. Populates existing_files_cache.
    
    Uses a persistent JSON cache (gemini_file_cache.json) to avoid re-listing files from
    the Gemini API on every server restart. Cached URIs are validated before use.
    """
    global existing_files_cache
    source_dir = os.path.join(DATA_DIR, "source_files")
    
    if not os.path.exists(source_dir) or not client:
        return

    print("[cache] Loading persistent file cache from disk...")
    uri_cache = _load_persistent_cache()  # {display_name: uri}
    cache_updated = False

    # Validate cached entries by checking they still exist in Gemini
    print(f"[cache] Validating {len(uri_cache)} cached file(s)...")
    valid_uri_cache = {}
    for display_name, uri in uri_cache.items():
        try:
            # Extract the file name (e.g. "files/abc123") from the URI
            file_id = "/".join(uri.split("/")[-2:])
            f = client.files.get(name=file_id)
            existing_files_cache[display_name] = f
            valid_uri_cache[display_name] = uri
        except Exception:
            print(f"  [cache] Evicting expired/missing file: {display_name}")
            cache_updated = True  # Will need to re-upload this file

    # If any cached entry was evicted, also check Gemini directly for any new uploads
    # we might have missed (e.g. uploaded from another process)
    if cache_updated or not valid_uri_cache:
        print("[cache] Fetching current file list from Gemini API...")
        try:
            for f in client.files.list():
                existing_files_cache[f.display_name] = f
                valid_uri_cache[f.display_name] = f.uri
        except Exception as e:
            print(f"  [cache] Failed to list Gemini files: {e}")

    for root, _, files in os.walk(source_dir):
        for filename in files:
            if filename.endswith(".pdf"):
                file_path = os.path.join(root, filename)
                subject = os.path.basename(root)
                display_name = f"{subject}_{filename}"
                
                if display_name in existing_files_cache:
                    print(f"Skipping {filename} (Already in Gemini database).")
                else:
                    print(f"Uploading {filename} (Subject: {subject})...")
                    try:
                        uploaded_file = client.files.upload(
                            file=file_path,
                            config=types.UploadFileConfig(display_name=display_name, mime_type="application/pdf")
                        )
                        print(f"  -> Uploaded as: {uploaded_file.uri}")
                        existing_files_cache[display_name] = uploaded_file
                        valid_uri_cache[display_name] = uploaded_file.uri
                        cache_updated = True
                    except Exception as e:
                        print(f"  -> Failed to upload {filename}: {e}")

    # Persist the updated cache to disk if anything changed
    if cache_updated or len(valid_uri_cache) != len(uri_cache):
        print(f"[cache] Saving updated cache ({len(valid_uri_cache)} entries) to disk...")
        _save_persistent_cache(valid_uri_cache)
    else:
        print("[cache] Cache is up-to-date. No disk write needed.")

def get_pdf_parts_for_context(subject: str, course_level: str, query_text: str = ""):
    """Returns a list of specific Gemini file parts/chunks for the requested subject and course.
       Uses vector embedding search (text-embedding-004) to filter top relevant chunks when query_text is present."""
    if not course_level:
        return []
        
    grade_match = "".join([c for c in course_level if c.isdigit()])
    if not grade_match:
        return []
        
    grade_num_padded = grade_match.zfill(2) # e.g. "03"
    
    # Define the list of expected file name patterns to look for in the cache
    expected_patterns = []
    if subject.lower() == "matematicas":
        expected_patterns.append(f"Aula_Matematicas_{grade_num_padded}_INTERIOR.pdf")
        if grade_match in ["3", "4", "5", "6"]:
            expected_patterns.append("LAMINAS.pdf")
    elif subject.lower() == "lengua":
        expected_patterns.append(f"Aula_Lengua_{grade_num_padded}_INTERIOR.pdf")
    elif subject.lower() == "valenciano":
        expected_patterns.append(f"AULA_VALENCIANO_{grade_match}.pdf")
    elif subject.lower() == "ingles":
        expected_patterns.append(f"Aula_english_{grade_num_padded}.pdf")
        expected_patterns.append(f"Aula_english_{grade_num_padded}_Part1.pdf")
        expected_patterns.append(f"Aula_english_{grade_num_padded}_Part2.pdf")
    else:
        expected_patterns.append(f"Aula_{subject.capitalize()}_{grade_num_padded}_INTERIOR.pdf")
        
    parts = []
    
    # Also load any RAG JSON documents in the subject source folder (e.g. reglas_acentuacion_lomloe_rag.json)
    subject_dir = os.path.join(DATA_DIR, "source_files", subject.lower())
    json_chunks_candidates = []

    if os.path.exists(subject_dir):
        for f_name in os.listdir(subject_dir):
            if f_name.endswith(".json") and not f_name.startswith("temario_"):
                json_path = os.path.join(subject_dir, f_name)
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict) and "chunks" in data:
                            doc_title = data.get("title", f_name)
                            for c in data["chunks"]:
                                c_text = c.get("content", "")
                                if c_text:
                                    json_chunks_candidates.append({
                                        "title": doc_title,
                                        "text": f"[{doc_title} - {c.get('topic', '')}] {c_text}"
                                    })
                        elif isinstance(data, dict) and "text" in data:
                            json_chunks_candidates.append({
                                "title": f_name,
                                "text": data["text"]
                            })
                except Exception as e:
                    print(f"Error reading RAG JSON {json_path}: {e}")

    # Apply Vector Search on RAG chunks if query_text is available
    if json_chunks_candidates:
        if query_text:
            try:
                from .vector_store import search_relevant_chunks
                top_chunks = search_relevant_chunks(query_text, json_chunks_candidates, top_k=3)
                combined = "\n\n".join([c["text"] for c in top_chunks])
                parts.append(types.Part(text=f"DOCUMENTO VERIFICADO RAG (SELECCIÓN VECTORIAL):\n{combined}"))
                print(f"[vector_search] Retornando los {len(top_chunks)} chunks más relevantes para '{query_text[:30]}...'")
            except Exception as ve:
                print(f"Vector search error: {ve}")
                combined = "\n\n".join([c["text"] for c in json_chunks_candidates[:5]])
                parts.append(types.Part(text=f"DOCUMENTO VERIFICADO RAG:\n{combined}"))
        else:
            combined = "\n\n".join([c["text"] for c in json_chunks_candidates[:5]])
            parts.append(types.Part(text=f"DOCUMENTO VERIFICADO RAG:\n{combined}"))

    # Prioritize Text Content fallback
    txt_filename = f"Aula_{subject.lower()}_{grade_num_padded}.txt"
    if subject.lower() == "ingles":
        txt_filename = f"Aula_english_{grade_num_padded}.txt"
        
    txt_path = os.path.join(DATA_DIR, "source_files", subject.lower(), txt_filename)
    if os.path.exists(txt_path):
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                text_content = f.read()
                parts.append(types.Part(text=f"CONTENIDO DEL LIBRO ({subject} {course_level}):\n{text_content}"))
                print(f"[speed] Using TEXT context for {subject} {grade_num_padded}.")
                return parts
        except Exception as e:
            print(f"Error reading text fallback for {txt_path}: {e}")

    # Fallback to PDF only if no text exists
    for pattern in expected_patterns:
        display_name = f"{subject}_{pattern}"
        cached_file = existing_files_cache.get(display_name)
        if cached_file:
            parts.append(types.Part(file_data=types.FileData(file_uri=cached_file.uri, mime_type="application/pdf")))
            
    return parts

# Load PDFs at startup to populate cache
if client:
    load_pdf_files_as_parts()

def get_db_question(subject: str, grade: int = None, bloque: str = None, contenido: str = None) -> str:
    """Extrae una pregunta aleatoria optimizada para bases de datos grandes."""
    import random as _random
    from sqlalchemy import func

    db = SessionLocal()
    try:
        norm_subject = normalize_text(subject)
        # Handle "mates" -> "matematicas" mapping
        if "matem" in norm_subject: norm_subject = "matematicas"
        
        print(f"[DB_DEBUG] Consulta: sub={norm_subject}, grade={grade}, bloque={bloque}")
        
        # 1. SQL-level filtering for performance
        query = db.query(models.Question).filter(
            models.Question.is_active == True,
            models.Question.is_verified == True,
            func.lower(models.Question.subject).contains(norm_subject)
        )
        
        if grade:
            query = query.filter(models.Question.grade == int(grade))
            
        all_q = query.all()
        
        if not all_q:
            print(f"[DB_DEBUG] CERO resultados SQL para {norm_subject} grado {grade}")
            return json.dumps({"error": f"No hay ejercicios verificados para {subject} - curso {grade}"})

        # 2. Python-level matching for Bloque/Contenido (Fuzzy)
        final_pool = all_q
        if bloque or contenido:
            norm_bloque = normalize_text(bloque)
            norm_cont = normalize_text(contenido)
            
            strict_pool = []
            for q in all_q:
                q_bloque = normalize_text(q.bloque or "")
                q_cont = normalize_text(q.contenido or "")
                
                match_b = (not norm_bloque) or (norm_bloque in q_bloque)
                match_c = (not norm_cont) or (norm_cont in q_cont)
                
                if match_b and match_c:
                    strict_pool.append(q)
            
            if strict_pool:
                final_pool = strict_pool
            else:
                print(f"[DB_DEBUG] Sin coincidencia de bloque. Usando pool de asignatura ({len(all_q)} items).")

        picked = _random.choice(final_pool)

        return json.dumps({
            "id": picked.id,
            "identifier": picked.identifier or "",
            "question": picked.question,
            "options": json.loads(picked.options),
            "answer": picked.answer,
            "visual_url": picked.visual_url,
            "audio_url": picked.audio_url
        }, ensure_ascii=False)
    finally:
        db.close()

def get_db_explanation(subject: str, grade: int = None, bloque: str = None, contenido: str = None, force_easier: bool = False) -> Optional[str]:
    """Busca una explicación verificada en la base de datos de Aula con normalización."""
    exp = get_db_explanation_obj(subject=subject, grade=grade, bloque=bloque, contenido=contenido)
    if exp:
        return (exp.easier_version or exp.text) if force_easier else exp.text
    return None

def get_db_explanation_obj(subject: str, grade: int = None, bloque: str = None, contenido: str = None):
    """Fetch Explanation model object directly with robust python-side accent-insensitive matching."""
    db = SessionLocal()
    try:
        norm_subject = normalize_text(subject)
        q = db.query(models.Explanation).filter(
            func.lower(models.Explanation.subject) == norm_subject,
            models.Explanation.is_active == True,
            models.Explanation.is_verified == True
        )
        if grade:
            q = q.filter((models.Explanation.grade == grade) | (models.Explanation.grade == None))
            
        candidates = q.order_by(models.Explanation.id.desc()).all()
        if not candidates:
            return None

        # Prioridad 1: Búsqueda por Contenido exacto/parcial (normalizado)
        if contenido:
            norm_cont = normalize_text(contenido)
            for exp in candidates:
                if exp.contenido and norm_cont in normalize_text(exp.contenido):
                    return exp

        # Prioridad 2: Búsqueda por Bloque (normalizado)
        if bloque:
            norm_bloque = normalize_text(bloque)
            for exp in candidates:
                if exp.bloque and norm_bloque in normalize_text(exp.bloque):
                    return exp

        # Prioridad 3: Búsqueda genérica por asignatura
        return candidates[0]
    finally:
        db.close()

# Limit for chat history to prevent slowness and context confusion
MAX_HISTORY_LENGTH = 6 

async def get_gemini_response(user_message: str, subject: str = "general", course_level: str = "", user_id: str = "default", reset_history: bool = False, mastery_stats: list = None, bloque: str = None, contenido: str = None) -> str:
    """Sends a message to Gemini using the new SDK and returns the response."""
    if not client:
        return "⚠️ Error: API Key de Gemini no configurada. Por favor, revisa el archivo .env.", False, {}

    try:
        # Build full conversation with memory history for this specific subject and user
        history_key = f"{user_id}_{subject}"
        if reset_history and history_key in chat_histories:
            del chat_histories[history_key]

        subject_history = chat_histories.setdefault(history_key, [])
        
        # Enforce history limit
        if len(subject_history) > MAX_HISTORY_LENGTH * 2: # roles are user, model pairs
            chat_histories[history_key] = subject_history[-(MAX_HISTORY_LENGTH * 2):]
            subject_history = chat_histories[history_key]

        messages = list(subject_history)
        
        if history_key not in chat_histories:
            chat_histories[history_key] = []
        
        subject_history = chat_histories[history_key]
        
        # Prepare context parts
        current_parts = []
        
        # --- PRE-CARGA DE DATOS TEÓRICOS ---
        db_explanation = None
        grade_val = None
        if course_level:
            grade_match = re.search(r'\d+', str(course_level))
            if grade_match: grade_val = int(grade_match.group())

        if subject != "general":
            try:
                # Fetch standard explanation
                db_explanation = get_db_explanation(subject=subject, grade=grade_val, bloque=bloque, contenido=contenido)
            except Exception as e:
                print(f"[RAG_ERROR] Fallo en prefetch inicial: {str(e)}")

        current_parts.append(types.Part(text=(
            "RECUERDA: Eres un profesor paciente y experto. "
            "Tu objetivo principal es enseñar la TEORÍA y proporcionar EJEMPLOS CLAROS. "
            "PROHIBIDO realizar o proponer ejercicios, tests o cuestionarios al alumno. "
            "Si el alumno tiene dudas, resuélvelas con ejemplos. "
            "Usa lenguaje neutro y cercano."
        )))
        
        # --- PREPARACIÓN DEL MANDATO DEL TURNO ---
        is_review = any(kw in user_message.lower() for kw in ["repasar", "repaso", "tema", "quien", "ayuda", "explicaci", "ejemplo"])
        turn_instruction = ""
        
        if is_review:
             turn_instruction = "\n[MANDATO] Empieza proporcionando o completando la lección teórica detallada. Si el alumno pide ejemplos, dáselos claramente explicados."
             if db_explanation:
                 turn_instruction += f"\nUSA ESTA TEORÍA VERIFICADA COMO BASE PRINCIPAL: {db_explanation}"
        
        modified_user_message = f"{user_message}\n{turn_instruction}" if turn_instruction else user_message
        
        import asyncio
        max_retries = 3
        retry_delay = 2
        response = None
        
        for attempt in range(max_retries):
            current_parts_loop = list(current_parts)
            
            # 1. Cargar Agente Especialista desde el Multi-Agent System
            from .multi_agent_system import router, AgenteAuditor
            specialist_agent = router.get_agent(subject)
            subject_rules = load_context_rules(subject)
            dynamic_instruction = specialist_agent.get_system_prompt(SYSTEM_INSTRUCTION, subject_rules or "")

            # 3. Inyectar Contexto
            context_info = f"\n\n### DASHBOARD DEL TUTOR:\n- Asignatura: {subject}\n- Curso: {course_level if course_level else 'Primaria'}"
            
            # --- CONTEXTO DEL LIBRO (PDF/Texto) ---
            book_context = get_pdf_parts_for_context(subject, course_level)
            current_parts_loop.extend(book_context)

            dynamic_instruction += context_info
            
            current_parts_loop.append(types.Part(text=modified_user_message))
            
            # Prepare final messages list
            messages = list(subject_history)
            messages.append(types.Content(role="user", parts=current_parts_loop))

            with open("rag_payload.txt", "w") as f:
                f.write(f"SYSTEM INSTRUCTION: {dynamic_instruction}\\n\\n")
                f.write(f"MESSAGES: {messages}\\n")

            try:
                current_client = get_client()
                response = await current_client.aio.models.generate_content(
                    model=MODEL_NAME,
                    contents=messages,
                    config=types.GenerateContentConfig(
                        system_instruction=dynamic_instruction,
                        temperature=0.0
                    )
                )
                break # Success!
            except Exception as e:
                err_str = str(e).upper()
                is_file_error = "403" in err_str or "PERMISSION_DENIED" in err_str or "FILE" in err_str
                is_transient = "503" in err_str or "UNAVAILABLE" in err_str or "429" in err_str
                
                if is_file_error and attempt < max_retries - 1:
                    if os.path.exists(CACHE_FILE):
                        try: os.remove(CACHE_FILE)
                        except: pass
                    global existing_files_cache
                    existing_files_cache = {}
                    load_pdf_files_as_parts()
                    await asyncio.sleep(1)
                    continue
                elif is_transient and attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2 
                    continue
                else:
                    raise e

        response_text = ""
        if response and response.candidates and response.candidates[0].content.parts:
            response_text = clean_ai_text(response.text)
        else:
            response_text = "⚠️ Lo siento, no he podido generar una respuesta."

        # Keep history in subjects dictionary
        subject_history.append(types.Content(role="user", parts=[types.Part(text=user_message)]))
        subject_history.append(types.Content(role="model", parts=[types.Part(text=response_text)]))
        
        return response_text, False, {}
    except Exception as e:
        import traceback
        load_dotenv(override=True)
        key = os.environ.get("GEMINI_API_KEY", "")
        key_masked = f"{key[:5]}...{key[-4:]}" if key else "NONE"
        with open("rag_error.log", "w") as f:
            f.write(f"API KEY USED BY SERVER: {key_masked}\n\n")
            f.write(traceback.format_exc())
        print(f"Gemini API Error: {e}")
        return "¡Ups! Algo ha fallado. Por favor, vuelve a intentarlo.", False, {}

def get_cached_explanation(db_session, subject: str, course_level: str, bloque: str, contenido: str, user_message: str):
    """Retrieve explanation from semantic cache if available."""
    if not db_session:
        return None
    try:
        norm_msg = normalize_text(user_message).strip()
        key = f"{normalize_text(subject)}_{normalize_text(course_level)}_{normalize_text(bloque)}_{normalize_text(contenido)}_{norm_msg}"
        cached = db_session.query(models.CachedExplanation).filter(models.CachedExplanation.cache_key == key).first()
        if cached:
            return cached.explanation_response
    except Exception as e:
        print("Cache lookup error:", e)
    return None

def save_cached_explanation(db_session, subject: str, course_level: str, bloque: str, contenido: str, user_message: str, response_text: str):
    """Save explanation to semantic cache."""
    if not db_session or not response_text:
        return
    try:
        norm_msg = normalize_text(user_message).strip()
        key = f"{normalize_text(subject)}_{normalize_text(course_level)}_{normalize_text(bloque)}_{normalize_text(contenido)}_{norm_msg}"
        existing = db_session.query(models.CachedExplanation).filter(models.CachedExplanation.cache_key == key).first()
        if not existing:
            cached = models.CachedExplanation(
                cache_key=key,
                subject=subject,
                course_level=course_level,
                bloque=bloque,
                contenido=contenido,
                prompt_query=user_message,
                explanation_response=response_text
            )
            db_session.add(cached)
            db_session.commit()
    except Exception as e:
        print("Cache save error:", e)

async def get_gemini_response_stream(
    user_message: str,
    subject: str = "lengua",
    course_level: str = "",
    user_id: str = "default_user",
    reset_history: bool = False,
    mastery_stats: list = None,
    bloque: str = "",
    contenido: str = "",
    db_session = None
):
    """Yields streaming SSE data chunks as Gemini generates the response in real-time, with semantic caching and multimodal image support."""
    # Multimodal image attachments disabled by user directive for clean text/schema focus
    grade_val = None
    if course_level:
        grade_match = re.search(r'\d+', str(course_level))
        if grade_match: grade_val = int(grade_match.group())

    is_easier_req = any(kw in user_message.lower() for kw in ["más fácil", "mas facil", "més fàcil", "versión fácil", "version facil", "adaptad"])
    is_example_req = any(kw in user_message.lower() for kw in ["ejemplo", "exemples", "otro ejemplo"])

    visual_url = None
    video_url = None
    exp_obj = None

    if subject != "general":
        try:
            exp_obj = get_db_explanation_obj(subject=subject, grade=grade_val, bloque=bloque, contenido=contenido)
            if exp_obj:
                video_url = exp_obj.video_url
            # Prioridad 1: Si pide Versión Fácil y EXISTE en BD -> Responder INMEDIATAMENTE con ella
            if exp_obj and is_easier_req and exp_obj.easier_version and exp_obj.easier_version.strip():
                saved_easier = exp_obj.easier_version.strip()
                v_url = exp_obj.easier_visual_url or exp_obj.visual_url
                yield f"data: {json.dumps({'text': saved_easier, 'visual_url': v_url, 'video_url': video_url})}\n\n"
                yield f"data: {json.dumps({'done': True, 'full_text': saved_easier, 'visual_url': v_url, 'video_url': video_url})}\n\n"
                return

            # Prioridad 2: Si pide Ejemplos y EXISTEN en BD -> Responder INMEDIATAMENTE con ellos
            if exp_obj and is_example_req and exp_obj.examples and exp_obj.examples.strip():
                ex_raw = exp_obj.examples.strip()
                try:
                    ex_list = json.loads(ex_raw)
                    if isinstance(ex_list, list):
                        formatted_ex = "### 💡 Ejemplos Prácticos:\n\n" + "\n\n".join([f"• {ex}" for ex in ex_list])
                    else:
                        formatted_ex = f"### 💡 Ejemplos Prácticos:\n\n{ex_raw}"
                except Exception:
                    formatted_ex = f"### 💡 Ejemplos Prácticos:\n\n{ex_raw}"
                v_url = exp_obj.examples_visual_url or exp_obj.visual_url
                yield f"data: {json.dumps({'text': formatted_ex, 'visual_url': v_url, 'video_url': video_url})}\n\n"
                yield f"data: {json.dumps({'done': True, 'full_text': formatted_ex, 'visual_url': v_url, 'video_url': video_url})}\n\n"
                return

            if exp_obj:
                visual_url = exp_obj.visual_url
        except Exception as e:
            print(f"[RAG_ERROR] Fallo en pre-fetch de lección: {str(e)}")

    # --- Check Semantic Cache Next ---
    cached_text = get_cached_explanation(db_session, subject, course_level, bloque, contenido, user_message)
    if cached_text:
        print(f"CACHE HIT [0 ms, 0 tokens]: {subject}/{course_level}/{bloque}/{contenido}")
        yield f"data: {json.dumps({'text': cached_text, 'visual_url': visual_url, 'video_url': video_url})}\n\n"
        yield f"data: {json.dumps({'done': True, 'full_text': cached_text, 'visual_url': visual_url, 'video_url': video_url})}\n\n"
        return

    history_key = f"{user_id}_{subject}"
    
    if reset_history and history_key in chat_histories:
        del chat_histories[history_key]

    subject_history = chat_histories.setdefault(history_key, [])

    current_parts = []
    
    turn_instruction = (
        "RECUERDA: Eres un profesor paciente y experto. "
        "Tu objetivo principal es enseñar la TEORÍA y proporcionar EJEMPLOS CLAROS. "
        "USA PÁRRAFOS CORTOS Y ABUNDANTES PUNTOS Y APARTE (\n\n) entre ideas para facilitar la lectura. "
        "PROHIBIDO realizar o proponer ejercicios, tests o cuestionarios al alumno. "
        "Si el alumno tiene dudas, resuélvelas con ejemplos. "
        "Usa lenguaje neutro y cercano."
    )

    db_explanation = None
    if exp_obj:
        if is_easier_req:
            db_explanation = f"[INSTRUCCIÓN: El alumno pide la versión adaptada/más fácil. Simplifica y explica de forma súper sencilla la lección]:\n{exp_obj.text}"
            visual_url = exp_obj.easier_visual_url or exp_obj.visual_url
        elif is_example_req:
            db_explanation = f"[INSTRUCCIÓN: El alumno pide ejemplos prácticos de la vida cotidiana para esta lección]:\n{exp_obj.text}"
            visual_url = exp_obj.examples_visual_url or exp_obj.visual_url
        else:
            db_explanation = exp_obj.text
            visual_url = exp_obj.visual_url

    from app.multi_agent_system import get_didactic_course_rules
    course_didactic_rules = get_didactic_course_rules(grade_val)
    if course_didactic_rules:
        turn_instruction += course_didactic_rules

    if db_explanation:
        turn_instruction += f"\n\n### TEORÍA MAESTRA VERIFICADA (UTILIZA ESTE TEXTO PARA LA EXPLICACIÓN):\n{db_explanation}"
    elif bloque or contenido:
        filter_context = f"[Contexto de Filtrado: Bloque '{bloque}', Contenido '{contenido}']\n"
        turn_instruction = filter_context + turn_instruction
        
    modified_user_message = f"{user_message}\n{turn_instruction}" if turn_instruction else user_message
    
    current_parts_loop = list(current_parts)
    
    # 1. Cargar Instrucciones Universales
    dynamic_instruction = SYSTEM_INSTRUCTION

    # 2. Cargar Agente Especialista
    subject_rules = load_context_rules(subject)
    if subject_rules:
        dynamic_instruction += f"\n\n*** AGENTE ESPECIALISTA: {subject.upper()} ***\n{subject_rules}\n"
    else:
        dynamic_instruction += f"\n\n[AVISO] Eres un tutor de {subject}. Céntrate en teoría y ejemplos."

    # 3. Inyectar Contexto
    context_info = f"\n\n### DASHBOARD DEL TUTOR:\n- Asignatura: {subject}\n- Curso: {course_level if course_level else 'Primaria'}"
    
    # --- CONTEXTO DEL LIBRO (PDF/Texto/JSON con Búsqueda Vectorial) ---
    book_context = get_pdf_parts_for_context(subject, course_level, query_text=user_message)
    current_parts_loop.extend(book_context)

    dynamic_instruction += context_info
    current_parts_loop.append(types.Part(text=modified_user_message))
    
    messages = list(subject_history)
    messages.append(types.Content(role="user", parts=current_parts_loop))

    current_client = get_client()
    full_response_text = ""
    try:
        stream = await current_client.aio.models.generate_content_stream(
            model=MODEL_NAME,
            contents=messages,
            config=types.GenerateContentConfig(
                system_instruction=dynamic_instruction,
                temperature=0.0
            )
        )
        async for chunk in stream:
            if chunk.text:
                full_response_text += chunk.text
                yield f"data: {json.dumps({'text': chunk.text, 'visual_url': visual_url, 'video_url': video_url})}\n\n"
        
        from .multi_agent_system import AgenteAuditor
        cleaned_text = AgenteAuditor.audit_and_clean(clean_ai_text(full_response_text), subject)
        subject_history.append(types.Content(role="user", parts=[types.Part(text=modified_user_message)]))
        subject_history.append(types.Content(role="model", parts=[types.Part(text=cleaned_text)]))
        
        # Save to semantic cache for future instant responses (0 ms, 0 tokens)
        if db_session:
            save_cached_explanation(db_session, subject, course_level, bloque, contenido, user_message, cleaned_text)

        yield f"data: {json.dumps({'done': True, 'full_text': cleaned_text, 'visual_url': visual_url, 'video_url': video_url})}\n\n"
    except Exception as e:
        import traceback
        print(f"Gemini Streaming Error: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

def upload_new_file_to_gemini(file_path: str, subject: str) -> bool:
    """Uploads a new PDF to Gemini and updates the cache."""
    if not client:
        return False
    try:
        filename = os.path.basename(file_path)
        print(f"Uploading {filename} for subject {subject}...")
        display_name = f"{subject}_{filename}"
        uploaded_file = client.files.upload(
            file=file_path,
            config=types.UploadFileConfig(display_name=display_name, mime_type="application/pdf")
        )
        existing_files_cache[display_name] = uploaded_file
        # Also persist the new entry to the on-disk cache
        uri_cache = _load_persistent_cache()
        uri_cache[display_name] = uploaded_file.uri
        _save_persistent_cache(uri_cache)
        return True
    except Exception as e:
        print(f"Error uploading file: {e}")
        return False
