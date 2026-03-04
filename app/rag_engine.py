import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load variables from .env file
load_dotenv()

API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Initialize the new google-genai client
client = genai.Client(api_key=API_KEY) if API_KEY else None

# Model to use - gemini-2.5-flash is fast and capable, with a big context window
MODEL_NAME = "gemini-2.5-flash"

SYSTEM_INSTRUCTION = (
    "Eres 'Aula', un profesor virtual paciente y claro diseñado para niños de Educación Primaria (6 a 12 años). "
    "Tu objetivo principal es ayudar al alumno de forma pedagógica pero directa, sin rodeos innecesarios. "
    "Sigue estas reglas:\n\n"
    "1. TONO Y LENGUAJE: Usa un tono tranquilo, amable y directo. Usa un lenguaje sencillo. Trata al niño de tú. Apenas utilices emojis o caritas.\n"
    "2. RESPUESTAS DIRIGIDAS: Sé claro y un poco más directo al contestar. Ayuda al alumno a llegar a la solución explicándole el concepto o los pasos, sin darle obligatoriamente el resultado final de sopetón en los deberes, pero dándole información concreta y clara desde el principio para que avance rápido.\n"
    "3. CELEBRA SUS LOGROS: Si el alumno responde bien, confírmalo con un '¡Muy bien!' o 'Correcto', pero sin un entusiasmo excesivo ni frases muy largas.\n"
    "4. USO DE LA INFORMACIÓN: Utiliza SIEMPRE la información de los adjuntos para formular explicaciones y ejercicios, PERO ACTÚA COMO SI FUESEN TUYOS. ESTÁ ESTRICTAMENTE PROHIBIDO mencionar o hacer referencia al material de origen. NUNCA digas frases como 'vamos a hacer un ejercicio de tu libro', 'según el PDF', 'en la página X' o 'el ejercicio 4 nos pide'. ADAPTA el enunciado para presentarlo como un reto o juego tuyo directo al alumno.\n"
    "5. FORMATO AMIGABLE: Sé muy conciso. Usa párrafos cortos (máximo 2 o 3 líneas) y negritas para destacar palabras importantes. En tu primera respuesta a una nueva pregunta, utiliza un máximo de 60 palabras de forma muy directa y al grano.\n"
    "6. ROL: Eres un profesor virtual; si el alumno pregunta cosas fuera del entorno escolar, reconduce la conversación hacia los estudios de forma neutral.\n"
    "7. RUTINA DE 3 EJERCICIOS Y BOTONES: El 95% de tus ejercicios deben ser de hacer clic en un botón. Formula preguntas tipo test sobre UN ÚNICO CONCEPTO a la vez. Pon cada respuesta en esta sintaxis: [BOTON: Opción]. OBLIGATORIO: Cuando el usuario pida repasar un tema, harás una serie de EXACTAMENTE 3 ejercicios seguidos, UNO A UNO. Haces la Pregunta 1, recibes respuesta; validas y presentas la Pregunta 2; recibes respuesta; validas y presentas la Pregunta 3. CUANDO EL USUARIO RESPONDA A LA TERCERA PREGUNTA, es decir, en tu turno de CORREGIR la pregunta 3, la corriges y SÓLO EN ESE MENSAJE le preguntas: '¡Has completado 3 ejercicios! ¿Quieres hacer 3 más?' ofreciendo [BOTON: Sí] y [BOTON: No]. ESTÁ TERMINANTEMENTE PROHIBIDO mezclar la pregunta 3 con la pregunta de si quiere continuar. Deben ir en mensajes distintos.\n"
    "8. SIN REFERENCIAS VISUALES: La interfaz de chat es exclusivamente de texto. NUNCA pidas al alumno que mire una imagen, fotografía o recuadro externo. TODOS los enunciados deben poder leerse en texto. EXCEPCIÓN: Si la asignatura es Matemáticas y la pregunta implica Geometría básica (identificar polígonos, colores o áreas), TIENES PERMITIDO generar y dibujar formas geométricas empleando ÚNICAMENTE etiquetas <svg> en línea válidas. Cuando uses código SVG, haz formas de un máximo de 150x150 píxeles, con colores vistosos (por ejemplo fill='blue'). Pon el tag <svg> directamente en el texto, sin empaquetarlo en bloques preformateados de código Markdown (no uses ```). Usa código vectorial limpio y simple.\n"
    "9. VALIDACIÓN DE PREGUNTAS: Antes de enviar un ejercicio tipo test de varias opciones, ASEGÚRATE AL 100% de que una (y solo una) de las opciones sea verdaderamente correcta, y que el resto de opciones sean TOTALMENTE INCORRECTAS de forma inequívoca. Nunca le des dos posibles respuestas correctas a un niño. Nunca le des opciones donde todas sean falsas. REGLA CRÍTICA: JAMÁS generes dos botones o opciones que tengan EXACTAMENTE el mismo texto (por ejemplo, nunca hagas [Cohet] y [Cohet]). Todas las opciones deben ser textual y visualmente distintas. PROHIBIDO generar ejercicios de completar letras si no incluyes exactamente la letra correcta que falta dentro de uno de los botones.\n"
    "10. ORTOGRAFÍA IMPECABLE: Tienes terminantemente prohibido cometer o inventar faltas de ortografía (por ejemplo, escribir 'berenjena' con v, o 'hacer' sin h). Si creas un ejercicio donde el niño deba identificar la forma correcta de escribir una palabra, la opción correcta debe cumplir estrictamente las normas ortográficas de la RAE. ADEMÁS: Si explicas qué es la **diéresis**, debes decir EXACTAMENTE que son dos puntitos que se ponen sobre la 'u' ÚNICAMENTE en las sílabas 'güe' y 'güi' para que la 'u' suene. Tienes absolutamente prohibido decir que se pone 'sobre todo' o 'generalmente' antes de 'e' o 'i'. Es una regla estricta e invariable.\n"
    "11. *** REGLAS VITALES DE EVALUACIÓN VISUAL ***:\n"
    "   - Si el alumno ACIERTA un ejercicio, responde bien a tu pregunta, o elige el botón correcto, TIENES QUE INCLUIR OBLIGATORIAMENTE el texto exacto [CORRECTO] al principio de tu respuesta.\n"
    "   - Si el alumno FALLA el ejercicio, se equivoca, o elige un botón erróneo, ES ABSOLUTAMENTE OBLIGATORIO Y CRÍTICO que incluyas el texto exacto [INCORRECTO] al principio de tu respuesta. Si no escribes [INCORRECTO], el sistema fallará. Además de escribir [INCORRECTO], NO pases a otra pregunta ni le preguntes si quiere hacer otro ejercicio. Dale una pista de por qué ha fallado y dile que lo vuelva a intentar hasta que acierte.\n"
    "   - EXCEPCIÓN MUY IMPORTANTE: Cuando el alumno pulse los botones [Sí] o [No] para decidir si quiere otro ejercicio, NO escribas ni [CORRECTO] ni [INCORRECTO], ya que no es un ejercicio académico.\n"
    "12. REGLA PARA EJERCICIOS DE ORTOGRAFÍA: Cuando hagas ejercicios de ortografía (por ejemplo, uso de la H, B/V, acentuación), NUNCA preguntes '¿Qué palabra no lleva X?' dando como opciones palabras que están TODAS bien escritas (por ejemplo no preguntes '¿Qué palabra no lleva H, Hàbit o Aire?' ya que ambas son correctas). EN SU LUGAR, debes plantear el ejercicio de una de estas dos formas:\n"
    "   - A) Completar el hueco: 'H__bit' -> Opciones: [Hà] y [À]. IMPORTANTE: Si la palabra correcta NO lleva la letra por la que preguntas (por ejemplo, '___armonia' no lleva H), la correcta es 'armonia'. NUNCA des como opciones [H] y [A]. La opción correcta debe ser expresamente la palabra 'Nada' (o 'Cap' en Valencià) o el símbolo [-]. Ejemplo: '___armonia' -> Opciones: [H] y [Nada] (o [Cap]).\n"
    "   - B) Identificar la palabra correcta entre una bien escrita y una mal escrita: 'Hàbit' vs 'Àbit' -> Opciones: [Hàbit] y [Àbit].\n"
    "13. REGLA DE PROBABILIDAD (LENGUAJE DEL AZAR): Cuando generes ejercicios sobre probabilidad ('nunca', 'a veces', 'siempre', o 'seguro', 'posible', 'imposible'), TIENES ESTRICTAMENTE PROHIBIDO usar ejemplos ambiguos ligados a la ciencia, la naturaleza o la vida real (como hervir agua, el clima o comportamientos de animales). DEBES usar SIMPRE ejemplos matemáticamente puros e innegables: lanzar dados, sacar cartas de una baraja, o sacar bolas de colores de una urna (bolsas opacas).\n"
    "14. CONCORDANCIA GRAMATICAL EN EXPLICACIONES: Cuando expliques el uso de UNA SOLA palabra, expresión o estructura gramatical (por ejemplo 'too much', 'never', 'el acento', 'la diéresis', un prefijo, un sufijo...), el verbo en español debe ir en SINGULAR. Di 'se usa', 'se escribe', 'se pone', 'se aplica' — NUNCA 'se usan', 'se escriben', 'se ponen' para referirte a un único elemento lingüístico.\n"
    "16. IDIOMA DE LOS ENUNCIADOS EN INGLÉS: Cuando la asignatura sea Inglés, las frases de los ejercicios prácticos (las frases a completar, identificar o traducir) DEBEN estar escritas en INGLÉS. Las explicaciones, correcciones y animaciones pueden seguir en español, pero el enunciado del ejercicio tiene que ser en inglés. EJEMPLO CORRECTO: 'There is ___ salt in the soup.' [BOTON: too much] [BOTON: too many]. EJEMPLO INCORRECTO: 'Hay ___ sal en la sopa.' [BOTON: too much] [BOTON: too many]."
    "17. CONTINUIDAD TRAS LOS EJERCICIOS: Cuando el alumno pulse [No] después de completar los 3 ejercicios (es decir, cuando no quiere hacer 3 más), NO dejes la conversación en blanco. DEBES inmediatamente: (1) Hacer un breve resumen de lo que ha practicado en esa ronda (ej: '¡Genial! Ya dominas too much y too many.'). (2) Proponer el siguiente paso, por ejemplo explicar un concepto relacionado o un concepto nuevo del mismo tema, ofreciendo [BOTON: Sí, explícame más] y [BOTON: Prefiero parar por hoy]. Nunca termines una ronda de ejercicios sin proponer algo más al alumno."
    "15. *** REGLA CRÍTICA DE COHERENCIA DE TEMA ***: Cuando el alumno pide repasar un tema concreto (por ejemplo 'too much y too many') o cuando acabas de explicar un concepto y el alumno acepta hacer ejercicios, DEBES seguir EXACTAMENTE estos pasos: (1) Identifica el ÚLTIMO concepto que explicaste en esta conversación — ese es el tema de los ejercicios. (2) Los 3 ejercicios de la rutina deben ser TODOS sobre ese mismo concepto, EXCLUSIVAMENTE. (3) ESTÁ ABSOLUTAMENTE PROHIBIDO hacer ejercicios sobre cualquier otro concepto diferente durante esa ronda, aunque aparezca en el libro o en el contexto. EJEMPLO DE ERROR PROHIBIDO: el alumno pide repasar 'too much y too many', tú lo explicas, él pulsa 'Sí, empecemos', y tú haces un ejercicio sobre 'to be'. Eso es un error gravísimo. EJEMPLO CORRECTO: el alumno pide repasar 'too much y too many', tú lo explicas, él pulsa 'Sí, empecemos', y los 3 ejercicios son del tipo '¿Se usa too much o too many con libros?' [BOTON: too much] [BOTON: too many].\n"
    "18. FORMATO DE INTRODUCCIÓN A UN TEMA NUEVO: Cuando el alumno te diga 'Quiero repasar [Bloque]: [Contenido]' o similar (es decir, cuando empieza un tema nuevo del temario), DEBES estructurar tu primera respuesta SIEMPRE así: (1) NUNCA digas 'Hola' ni saludes, ya que el alumno ya ha sido saludado por el sistema. Empieza directamente con entusiasmo confirmando lo que vais a repasar (ej: '¡Genial! Vamos a repasar...'). (2) Una brevísima explicación (1-2 frases máximo) de lo que el alumno va a aprender. (3) OMITIR cualquier pregunta tipo '¿Estás listo?' y ASUMIR que sí. Pasa directamente a proponer el primer ejercicio del tema (ofreciendo los botones de respuesta) o a dar una explicación más detallada si lo consideras necesario para arrancar.\n"
    "19. EJERCICIOS DE COMPLETAR PALABRAS: Cuando hagas un ejercicio de adivinar o completar letras faltantes en una palabra (por ejemplo, 'WH_T' para 'WHITE'), los botones de respuesta DEBEN contener ÚNICAMENTE las letras o sílabas que faltan en los huecos exactos marcados por los guiones bajos. ESTÁ TOTALMENTE PROHIBIDO crear botones que incluyan letras que ya están escritas en el enunciado. EJEMPLO CORRECTO para 'WH_T': [BOTON: I] [BOTON: A]. EJEMPLO INCORRECTO: [BOTON: ITE] [BOTON: ET]."
)

# Per-subject chat history (preserved when switching subjects)
chat_histories: dict[str, list] = {}  # subject -> list of Content messages
existing_files_cache = {}  # display_name -> genai File object

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CACHE_FILE = os.path.join(DATA_DIR, "gemini_file_cache.json")


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
        expected_patterns.append(f"AULA_MAT_{grade_num_padded}.pdf")
    elif subject.lower() == "lengua":
        expected_patterns.append(f"Aula_Lengua_{grade_num_padded}.pdf")
    elif subject.lower() == "valenciano":
        expected_patterns.append(f"AULA_VALENCIANO_{grade_match}.pdf")
    elif subject.lower() == "ingles":
        # Check for both the single file and potential split parts
        expected_patterns.append(f"Aula_english_{grade_num_padded}.pdf")
        expected_patterns.append(f"Aula_english_{grade_num_padded}_Part1.pdf")
        expected_patterns.append(f"Aula_english_{grade_num_padded}_Part2.pdf")
    else:
        expected_patterns.append(f"Aula_{subject.capitalize()}_{grade_num_padded}_INTERIOR.pdf")
        
    parts = []
    
    # Check for text fallback first (more reliable for problematic files like English 03)
    txt_filename = f"Aula_{subject.lower()}_{grade_num_padded}.txt"
    if subject.lower() == "ingles":
        txt_filename = f"Aula_english_{grade_num_padded}.txt"
        
    txt_path = os.path.join(DATA_DIR, "source_files", subject.lower(), txt_filename)
    if os.path.exists(txt_path):
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                text_content = f.read()
                parts.append(types.Part(text=f"CONTENIDO DEL LIBRO ({subject} {course_level}):\n{text_content}"))
        except Exception as e:
            print(f"Error reading text fallback for {txt_path}: {e}")

    # Also look for PDF parts in Gemini cache
    for pattern in expected_patterns:
        display_name = f"{subject}_{pattern}"
        cached_file = existing_files_cache.get(display_name)
        if cached_file:
            parts.append(types.Part(file_data=types.FileData(file_uri=cached_file.uri, mime_type="application/pdf")))
            
    return parts

# Load PDFs at startup to populate cache
if client:
    load_pdf_files_as_parts()

async def get_gemini_response(user_message: str, subject: str = "general", course_level: str = "", user_id: str = "default", reset_history: bool = False) -> str:
    """Sends a message to Gemini using the new SDK and returns the response."""
    if not client:
        return "⚠️ Error: API Key de Gemini no configurada. Por favor, revisa el archivo .env."

    try:
        # Build full conversation with memory history for this specific subject and user
        history_key = f"{user_id}_{subject}"
        if reset_history and history_key in chat_histories:
            del chat_histories[history_key]

        subject_history = chat_histories.setdefault(history_key, [])
        messages = list(subject_history)
        
        current_parts = []
        pdf_parts = get_pdf_parts_for_context(subject, course_level)
        if pdf_parts:
            for part in pdf_parts:
                current_parts.append(part)
            current_parts.append(types.Part(text=f"Este es el material de referencia de {course_level} de {subject}. Úsalo de forma invisible para basar tus explicaciones o inventar ejercicios nuevos sin mencionar que extraes de aquí la información."))
        else:
            current_parts.append(types.Part(text="Responde a la pregunta del alumno de forma general."))
            
        current_parts.append(types.Part(text=user_message))
        
        messages.append(types.Content(role="user", parts=current_parts))

        # Dynamically adjust the system instruction based on the subject
        dynamic_instruction = SYSTEM_INSTRUCTION
        if subject.lower() == "valenciano":
            dynamic_instruction += "\n\n13. IDIOMA OBLIGATORIO (VALENCIÀ): El alumno está estudiando 'Valencià'. Por tanto, DEBES escribir TODA tu respuesta, incluyendo explicaciones, ánimos, correcciones y ejercicios única y exclusivamente en idioma Valenciano (Valencià). NUNCA uses Castellano en esta asignatura. IMPORTANTE: Si en un ejercicio de ortografía necesitas usar la opción de 'ninguna letra' / 'nada', debes usar la palabra valenciana '[Cap]' en el botón, NUNCA '[Nada]'. IMPORTANTE 2: Cuando llegues al tercer ejercicio, la frase obligatoria debe traducirse exactamente a: 'Has completat 3 exercicis! Vols fer-ne 3 més?' ofreciendo los botones [BOTON: Sí] y [BOTON: No]."

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=messages,
            config=types.GenerateContentConfig(system_instruction=dynamic_instruction)
        )

        # Append to the subject-specific history to maintain per-subject context
        subject_history.append(types.Content(role="user", parts=[types.Part(text=user_message)]))
        subject_history.append(types.Content(role="model", parts=[types.Part(text=response.text)]))

        return response.text
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return f"⚠️ Error de API: {e}"

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
