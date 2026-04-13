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

# Load variables from .env file
load_dotenv()

API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Initialize the new google-genai client
client = genai.Client(api_key=API_KEY) if API_KEY else None

# Model to use - gemini-2.5-flash is the most current model in your account list
MODEL_NAME = "gemini-2.5-flash"

def clean_ai_text(text: str) -> str:
    """Removes segments that only contain punctuation or artifacts like '¡!'."""
    if not text:
        return text
    
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

1. INICIO DE REPASO:
   USUARIO: "Quiero repasar los sustantivos."
   TUTOR: "¡Genial! Los sustantivos son las palabras que usamos para nombrar todo lo que nos rodea: personas, animales, objetos o lugares. Por ejemplo: **casa**, **león**, o **Sofía**. --- Ejercicio 1/3: ¿Cuál de estas palabras es un sustantivo? [BOTON: Correr] [BOTON: Azul] [BOTON: Gato]"

2. CORRECCIÓN POSITIVA:
   USUARIO: "Resta" (en un problema de suma)
   TUTOR: "[INCORRECTO] ¡Casi! Fíjate bien: si queremos saber cuánto tenemos en **total** al juntar dos cosas, lo que hacemos es **sumar**. ¡Inténtalo de nuevo! ¿Qué operación usas para juntar?"
"""

SYSTEM_INSTRUCTION = f"""
Eres 'Aula', un tutor experto de primaria. Tu misión es ayudar a niños de 6 a 12 años ÚNICAMENTE con los contenidos verificados de la base de datos.

### EL MANDATO SUPREMO (PROHIBIDO INVENTAR):
1. **ENTORNO CERRADO**: Tienes terminantemente prohibido usar tus conocimientos generales de IA para inventar ejercicios o explicaciones. 
2. **SOLO BASE DE DATOS**: Extrae preguntas y explicaciones ÚNICAMENTE de la base de datos y los archivos que se te proporcionan en el DASHBOARD.
3. **BLOQUEO DE CONTENIDO**: Si en el Dashboard dice "NO hay preguntas verificadas", NO puedes poner ningún ejercicio. Limítate a dar una explicación teórica basada en la 'FUENTE DE VERDAD' proporcionada y termina la conversación ahí para ese tema. 
4. **PROHIBIDO INTERNET**: No busques en internet ni asumas datos externos.

### REGLAS DE TRABAJO:
- **IDENTIFICADORES [ID: código]**: Es OBLIGATORIO incluir el código de la pregunta al final de cada enunciado extraído de la base de datos.
- **FORMATO DE BOTONES**: Cada ejercicio debe tener botones: [BOTON: Texto].
- **RESPUESTA_CORRECTA**: Incluye [RESPUESTA_CORRECTA: texto] al final de cada ejercicio para evaluación interna.
- **SERIES DE 3**: Trabaja en grupos de 3 ejercicios. Tras el 3/3, pregunta: '¿Quieres seguir?'.
- **NEGRILLA**: Usa **negrita** para conceptos clave.
- **TONO**: Sé paciente y motivador, pero neutro (no uses 'campeón' o 'niño').

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

def get_pdf_parts_for_context(subject: str, course_level: str):
    """Returns a list of specific Gemini file parts for the requested subject and course, using the cache.
       Supports multiple parts for the same course (e.g. Part1, Part2)."""
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
        # Check for both the single file and potential split parts
        expected_patterns.append(f"Aula_english_{grade_num_padded}.pdf")
        expected_patterns.append(f"Aula_english_{grade_num_padded}_Part1.pdf")
        expected_patterns.append(f"Aula_english_{grade_num_padded}_Part2.pdf")
    elif subject.lower() == "competencia_lectora":
        expected_patterns.append(f"CL_{grade_match}_corregido.pdf")
    else:
        expected_patterns.append(f"Aula_{subject.capitalize()}_{grade_num_padded}_INTERIOR.pdf")
        
    parts = []
    
    # Prioritize Text Content (Much faster processing + lower token usage)
    txt_filename = f"Aula_{subject.lower()}_{grade_num_padded}.txt"
    if subject.lower() == "ingles":
        txt_filename = f"Aula_english_{grade_num_padded}.txt"
        
    txt_path = os.path.join(DATA_DIR, "source_files", subject.lower(), txt_filename)
    if os.path.exists(txt_path):
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                text_content = f.read()
                parts.append(types.Part(text=f"CONTENIDO DEL LIBRO ({subject} {course_level}):\n{text_content}"))
                # If we have the text, we return EARLY to avoid sending the heavy PDF too
                print(f"[speed] Using TEXT context for {subject} {grade_num_padded} - Skipping PDF.")
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
    import unicodedata
    import random as _random
    from sqlalchemy import func

    def normalize_text(text):
        if not text: return ""
        return "".join(c for c in unicodedata.normalize('NFD', str(text)) if unicodedata.category(c) != 'Mn').lower()

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

def get_db_explanation(subject: str, grade: int = None, bloque: str = None, contenido: str = None) -> Optional[str]:
    """Busca una explicación verificada en la base de datos de Aula con normalización."""
    import unicodedata
    def normalize_text(text):
        if not text: return ""
        return "".join(c for c in unicodedata.normalize('NFD', str(text)) if unicodedata.category(c) != 'Mn').lower()

    db = SessionLocal()
    try:
        norm_subject = normalize_text(subject)
        # Only verified explanations (Rule 1)
        q = db.query(models.Explanation).filter(
            func.lower(models.Explanation.subject) == norm_subject,
            models.Explanation.is_active == True,
            models.Explanation.is_verified == True
        )
        
        if grade:
            q = q.filter((models.Explanation.grade == grade) | (models.Explanation.grade == None))
            
        # Prioridad 1: Búsqueda por Contenido exacto (normalizado)
        if contenido:
            norm_cont = normalize_text(contenido)
            q_cont = q.filter(func.lower(models.Explanation.contenido).contains(norm_cont))
            exp = q_cont.order_by(models.Explanation.id.desc()).first()
            if exp: return exp.text

        # Prioridad 2: Búsqueda por Bloque (normalizado)
        if bloque:
            norm_bloque = normalize_text(bloque)
            q_bloque = q.filter(func.lower(models.Explanation.bloque).contains(norm_bloque))
            exp = q_bloque.order_by(models.Explanation.id.desc()).first()
            if exp: return exp.text

        # Prioridad 3: Búsqueda genérica por asignatura (normalizada)
        exp = q.order_by(models.Explanation.id.desc()).first()
        return exp.text if exp else None
    finally:
        db.close()

# Limit for chat history to prevent slowness and context confusion
MAX_HISTORY_LENGTH = 6 

async def get_gemini_response(user_message: str, subject: str = "general", course_level: str = "", user_id: str = "default", reset_history: bool = False, mastery_stats: list = None, bloque: str = None, contenido: str = None, exercise_num: int = 0) -> str:
    """Sends a message to Gemini using the new SDK and returns the response."""
    if not client:
        return "⚠️ Error: API Key de Gemini no configurada. Por favor, revisa el archivo .env."

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
        
        # Add a clear separator if there's history
        if mastery_stats:
            stats_text = "Mastery stats for the user: " + ", ".join([f"{s['contenido']} ({s['bloque']}): {s['rate']}%" for s in mastery_stats])
            current_parts.append(types.Part(text=stats_text))

        pdf_parts = get_pdf_parts_for_context(subject, course_level)
        if pdf_parts:
            for part in pdf_parts:
                current_parts.append(part)

        # ── EXPLANATION SOURCE OF TRUTH (NEW ADAPTIVE LOGIC) ──
        # If it's a review turn, search for verified theory in DB
        db_explanation = None
        if any(kw in user_message.lower() for kw in ["repasar", "repaso", "tema", "quien", "ayuda", "explicaci"]):
            # Try to infer content from previous messages or user message
            # Try to infer content: anything after "repasar", "tema de", etc.
            contenido_inferido = ""
            # Priority 1: After ":" or "tema de"
            match = re.search(r'(?:repasar|tema de?|estudiar)[:\s]+([\w\s]{3,})', user_message.lower())
            if match:
                contenido_inferido = match.group(1).strip()
            else:
                # Priority 2: Generic "repasar X"
                match = re.search(r'repasar\s+([\w\s]{3,})', user_message.lower())
                if match:
                    contenido_inferido = match.group(1).strip()
            
            print(f"[DEBUG] Inferido/Enviado: '{contenido if contenido else contenido_inferido}' for message: '{user_message}'")
            db_explanation = get_db_explanation(subject, grade=None, bloque=bloque, contenido=contenido if contenido else contenido_inferido)
            if db_explanation:
                print(f"[DEBUG] Found DB Explanation for '{contenido_inferido}'")
            else:
                print(f"[DEBUG] No DB Explanation for '{contenido_inferido}'. Using PDF Fallback.")

        # Final instruction reminder
        current_parts.append(types.Part(text=(
            "RECUERDA: (1) Si el alumno pide un tema nuevo o dice 'repasar' y ya has saludado antes, PROHIBIDO saludar de nuevo. DEBES EMPEZAR SIEMPRE CON LA Explicación:. "
            "(2) DEBES USAR PALABRAS REALES. (3) PROHIBIDO mencionar temas, lecciones, páginas o actividades. "
            "(4) AISLAMIENTO DE EJERCICIOS: Todo ejercicio debe ir precedido por '---'. La burbuja del ejercicio debe contener ÚNICAMENTE el enunciado y las opciones. PROHIBIDO incluir mensajes de ánimo, explicaciones, intros o despedidas en la misma burbuja que el ejercicio. "
            "(5) ESTRUCTURA DE MENSAJE: Si das teoría y luego un ejercicio, el formato OBLIGATORIO es: [Texto de Explicación] \n---\n Ejercicio X/3: [Solo el enunciado]. "
            "(6) NEUTRO: Prohibido decir 'campeón', 'listo' o 'niño'. Usa lenguaje neutro. "
            "(7) DATA PREFERENCE: Prioriza SIEMPRE la base de datos. Si hay una 'CONTENIDO_VERIFICADO_A_USAR' en el DASHBOARD, es OBLIGATORIO usarla PALABRA POR PALABRA. PROHIBIDO inventar o parafrasear. "
            "(8) IDENTIFICADOR: Si usas la 'Pregunta disponible', DEBES incluir al final del enunciado el código [ID: código] tal cual viene en los datos. "
            "(9) PRECISIÓN: Verifica 2 veces antes de poner [INCORRECTO]. "
            "(10) MANDATO SUPREMO: EMPIEZA SIEMPRE con Explicación: antes de cualquier ejercicio nuevo. El ejercicio va después del '---' solo. PROHIBIDO decidir cuántos ejercicios hay o si la tanda ha terminado: eso lo controla el sistema automáticamente."
        )))
        
        # Combine user message with history
        messages = list(subject_history)
        
        # Prepare Turn-Specific Instruction (Compact & Anti-Redundancy)
        is_review = any(kw in user_message.lower() for kw in ["repasar", "repaso", "tema", "quien", "ayuda", "explicaci"])
        is_continuation = any(kw in user_message.lower() for kw in ["si", "siguiente", "otro", "vale", "continu", "mas"])
        is_evaluation = "[CORRECTO]" in user_message or "[INCORRECTO]" in user_message
        
        turn_instruction = ""
        is_option_chosen = "[OPCION_ELEGIDA]" in user_message
        if is_option_chosen and exercise_num > 0:
            next_num = exercise_num + 1
            if next_num <= 3:
                turn_instruction = (
                    f"\n[MANDATO] El alumno acaba de responder. Evalúa brevemente (máximo 2 frases). "
                    f"Después, usa '---' y presenta EXACTAMENTE el Ejercicio {next_num}/3 con la Pregunta disponible. "
                    f"PROHIBIDO usar otro número de ejercicio."
                )
            else:
                # exercise_num == 3, this is evaluation of the last one — JS will add the 'Continue?' bubble
                turn_instruction = (
                    f"\n[MANDATO] El alumno acaba de responder al último ejercicio (3/3). "
                    f"Evalúa brevemente (máximo 2 frases). PROHIBIDO añadir '¿Quieres seguir?' ni preguntas de continuidad: eso lo gestiona el sistema."
                )
        elif is_evaluation:
             turn_instruction = "\n[MANDATO] Verifica con extremo cuidado (Regla 34). Empieza SIEMPRE con [CORRECTO] o [INCORRECTO]."
        elif is_review:
             # Initial review request: Full Theory
             turn_instruction = "\n[MANDATO] Empieza OBLIGATORIAMENTE con la lección teórica detallada (Regla 2). Luego '---' y el primer ejercicio."
             if db_explanation:
                 turn_instruction += f"\nUSA ESTA TEORÍA VERIFICADA: {db_explanation}"
        elif is_continuation:
             # Continuous exercises: Short reminder only to avoid verbatim repetition
             turn_instruction = "\n[MANDATO] NO repitas la misma explicación de antes palabra por palabra. Da un breve recordatorio o pista de máximo 2 frases. Luego '---' y el ejercicio."
        
        modified_user_message = f"{user_message}\n{turn_instruction}" if turn_instruction else user_message
        
        # Search for a relevant question in the DB proactively to avoid tool calling (2x speed)
        prefetched_question = None
        if subject != "general":
            try:
                # Extract numeric grade from string like "1" or "1º"
                grade_val = None
                if course_level:
                    grade_match = re.search(r'\d+', str(course_level))
                    if grade_match:
                        grade_val = int(grade_match.group())
                
                print(f"[RAG_FLOW] Iniciando búsqueda de pregunta: sub={subject}, grade={grade_val}")
                prefetched_raw = get_db_question(subject=subject, grade=grade_val, bloque=bloque, contenido=contenido)
                prefetched_question = json.loads(prefetched_raw)
                
                # PREFETCH EXPLANATION - New seal of truth
                db_explanation = get_db_explanation(subject=subject, grade=grade_val, bloque=bloque, contenido=contenido)
            except Exception as e:
                print(f"[RAG_ERROR] Fallo en prefetch de datos DB: {str(e)}")
                db_explanation = None
                pass

        # Generate model response (WITH AUTOMATIC RETRIES for 503 high demand or 403 file errors)
        import asyncio
        max_retries = 3
        retry_delay = 2
        response = None
        
        for attempt in range(max_retries):
            # RE-PREPARE prompts and parts on every attempt to ensure file URIs are fresh if cache was cleared
            current_parts = []
            
            # 1. Cargar Instrucciones Universales
            dynamic_instruction = SYSTEM_INSTRUCTION

            # 2. Cargar Agente Especialista
            subject_rules = load_context_rules(subject)
            if subject_rules:
                dynamic_instruction += f"\n\n*** AGENTE ESPECIALISTA: {subject.upper()} ***\n{subject_rules}\n"
            else:
                dynamic_instruction += f"\n\n[AVISO] Eres un tutor de {subject}. Sigue las reglas generales de pedagogía."

            # 3. Inyectar Contexto de Clase (Oculto)
            context_info = f"\n\n### DASHBOARD DEL TUTOR (DATOS REALES):\n- Asignatura: {subject}\n- Curso: {course_level if course_level else 'Primaria'}"
            if mastery_stats:
                context_info += f"\n- Debilidades del alumno: {json.dumps(mastery_stats, ensure_ascii=False)}"
            
            # --- CONTEXTO DEL LIBRO (PDF/Texto) ---
            book_context = get_pdf_parts_for_context(subject, course_level)
            current_parts.extend(book_context)

            if prefetched_question and "question" in prefetched_question:
                context_info += f"\n\n### [MANDATO_SUPREMO] CONTENIDO_VERIFICADO_A_USAR:\n"
                context_info += f"ENUNCIADO: {prefetched_question['question']}\n"
                context_info += f"OPCIONES: {json.dumps(prefetched_question['options'], ensure_ascii=False)}\n"
                context_info += f"RESPUESTA_CORRECTA: {prefetched_question['answer']}\n"
                context_info += f"IDENTIFICADOR: {prefetched_question.get('identifier', 'S/N')}\n"
                context_info += "\n[INSTRUCCIÓN] Usa este enunciado EXACTAMENTE palabra por palabra. Este contenido está VERIFICADO por un administrador y es OBLIGATORIO usarlo."
            else:
                context_info += f"\n\n### [BLOQUEO_TOTAL_DE_GENERACIÓN]\n"
                context_info += "ADVERTENCIA: No se han encontrado contenidos verificados para esta consulta.\n"
                context_info += "MANDATO: Tienes TERMINANTEMENTE PROHIBIDO inventar un ejercicio. Solo puedes mostrar contenido marcado como 'Verificado' en la base de datos."
            
            dynamic_instruction += context_info

            # Turn-specific mandate
            mandate_text = ""
            if is_evaluation:
                 mandate_text = "[MANDATO_CRÍTICO] VERIFICA con extremo cuidado (Regla 34). Empieza SIEMPRE con [CORRECTO] o [INCORRECTO]."
            elif is_review:
                 mandate_text = "[MANDATO_CRÍTICO] Empieza SIEMPRE con la lección teórica detallada. Luego '---' y el primer ejercicio."
                 if db_explanation:
                      mandate_text += f"\n\n[FUENTE_DE_VERDAD_TEÓRICA] Usa esta explicación EXACTAMENTE PALABRA POR PALABRA: {db_explanation}\nPROHIBIDO parafrasear, resumir, 'corregir' o cambiar el texto. Úsalo íntegro tal cual. NO añadas ni una sola palabra de tu propia cosecha."

            if mandate_text:
                 current_parts.append(types.Part(text=f"\n\n*** {mandate_text} ***"))
            
            current_parts.append(types.Part(text=modified_user_message))
            
            # Prepare final messages list
            messages = list(subject_history)
            messages.append(types.Content(role="user", parts=current_parts))

            try:
                response = await client.aio.models.generate_content(
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
                    print(f"[RETRY] 403 File error detected. Clearing cache and re-uploading context...")
                    if os.path.exists(CACHE_FILE):
                        try: os.remove(CACHE_FILE)
                        except: pass
                    global existing_files_cache
                    existing_files_cache = {}
                    load_pdf_files_as_parts()
                    # The next loop iteration will naturally pick up the new files via get_pdf_parts_for_context()
                    await asyncio.sleep(1)
                    continue
                elif is_transient and attempt < max_retries - 1:
                    print(f"[RETRY] Servidor saturado (503/429). Reintento {attempt + 1}/{max_retries}...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2 
                    continue
                else:
                    raise e

        response_text = ""
        is_correct = False
        if response.candidates and response.candidates[0].content.parts:
            # Direct response (clean)
            response_text = clean_ai_text(response.text)
            # Only detect correctness when the user clicked an interactive button
            # and look for the STRUCTURED TAG at the start of the raw response
            is_button_evaluation = "[OPCION_ELEGIDA]" in user_message
            if is_button_evaluation:
                is_correct = bool(re.match(r'^\s*\[(?:CORRECTO|CORRECTE|CORRECT)\]', response.text, re.IGNORECASE))
            else:
                is_correct = False
        else:
            response_text = "⚠️ Lo siento, no he podido generar una respuesta."

        # Final safety check: ensure "¿Quieres seguir?" is ALWAYS separated by ---
        if "Ejercicio 3/3" in response_text and "¿Quieres seguir?" in response_text:
            if "---" not in response_text:
                response_text = response_text.replace("¿Quieres seguir?", "---\n¿Quieres seguir?")
            elif response_text.find("---") > response_text.find("¿Quieres seguir?"):
                response_text = response_text.replace("¿Quieres seguir?", "---\n¿Quieres seguir?")

        # Keep history in subjects dictionary (Internal state)
        subject_history.append(types.Content(role="user", parts=[types.Part(text=user_message)]))
        subject_history.append(types.Content(role="model", parts=[types.Part(text=response_text)]))

        media_info = {
            "visual_url": prefetched_question.get("visual_url") if prefetched_question else None,
            "audio_url": prefetched_question.get("audio_url") if prefetched_question else None
        }
        
        return response_text, is_correct, media_info
    except Exception as e:
        err_str = str(e).upper()
        print(f"Gemini API Error: {e}")
        if "503" in err_str or "UNAVAILABLE" in err_str or "TIMED OUT" in err_str:
            return "El servidor de IA está temporalmente ocupado. Por favor, inténtalo de nuevo en unos segundos. 🙏", False, {}
        if "429" in err_str or "QUOTA" in err_str or "RESOURCE_EXHAUSTED" in err_str:
            return "Hemos alcanzado el límite de consultas. Por favor, espera un momento e inténtalo de nuevo. ⏳", False, {}
        return "Ha ocurrido un error inesperado. Por favor, inténtalo de nuevo. 🔄", False, {}

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
