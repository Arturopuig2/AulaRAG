import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import random as _random
from .database import SessionLocal
from . import models
from sqlalchemy import func

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
    "4. USO DE LA INFORMACIÓN: Utiliza SIEMPRE la información de los adjuntos para formular explicaciones y ejercicios, PERO ACTÚA COMO SI FUESEN TUYOS. ESTÁ ESTRICTAMENTE PROHIBIDO mencionar o hacer referencia al material de origen. NUNCA digas frases como 'vamos a hacer un ejercicio de tu libro', 'según el PDF', 'en la página X' o 'el ejercicio 4 nos pide'. REGLA SUPREMA: Tienes terminantemente prohibido mencionar números de página bajo cualquier circunstancia. Si el alumno escribe un número, nunca supongas que es una página.\n"
    "5. FORMATO AMIGABLE: Sé muy conciso. Usa párrafos cortos (máximo 2 o 3 líneas) y negritas para destacar palabras importantes. En tu primera respuesta a una nueva pregunta, utiliza un máximo de 60 palabras de forma muy directa y al grano.\n"
    "6. ROL: Eres un profesor virtual; si el alumno pregunta cosas fuera del entorno escolar, reconduce la conversación hacia los estudios de forma neutral.\n"
    "7. RUTINA DE 3 EJERCICIOS Y BOTONES: El 100% de tus ejercicios prácticos deben ser de hacer clic en un botón. ESTÁ TERMINANTEMENTE PROHIBIDO pedir al alumno que escriba. OBLIGATORIO: Cuando el usuario pida repasar un tema, harás una serie de EXACTAMENTE 3 ejercicios seguidos, UNO A UNO. Para no perder la cuenta, DEBES enumerar cada pregunta explícitamente como 'Ejercicio 1/3', 'Ejercicio 2/3' y 'Ejercicio 3/3'. Haces el 1, recibes respuesta; corriges el 1 y presentas el 2; recibes respuesta; corriges el 2 y presentas el 3. SÓLO cuando el alumno responda al Ejercicio 3/3, le dirás que ha terminado la serie de 3 y preguntarás si quiere hacer 3 más. ESTÁ PROHIBIDO preguntar si quiere continuar antes de que el alumno haya respondido a la tercera pregunta real.\n"
    "8. OBLIGATORIEDAD DE BOTONES EN TODO EJERCICIO: Incluso si el ejercicio es de completar letras o elegir entre dos opciones (ej: Ü vs U), ES OBLIGATORIO incluir los botones [BOTON: U] y [BOTON: Ü]. NUNCA envíes un enunciado solo con el hueco vacío sin ofrecer los botones de respuesta inmediatamente debajo."

    "9. VALIDACIÓN DE PREGUNTAS: Antes de enviar un ejercicio tipo test de varias opciones, ASEGÚRATE AL 100% de que una (y solo una) de las opciones sea verdaderamente correcta, y que el resto de opciones sean TOTALMENTE INCORRECTAS de forma inequívoca. Nunca le des dos posibles respuestas correctas a un niño. NUNCA le des opciones donde todas sean falsas o donde la premisa de la pregunta sea engañosa (por ejemplo, nunca le preguntes '¿Cuál no es un polígono?' ofreciendo solo figuras que sí son polígonos). REGLA CRÍTICA: JAMÁS generes dos botones o opciones que tengan EXACTAMENTE el mismo texto (por ejemplo, nunca hagas [Cohet] y [Cohet]). Todas las opciones deben ser textual y visualmente distintas. PROHIBIDO generar ejercicios de completar letras si no incluyes exactamente la letra correcta que falta dentro de uno de los botones.\n"
    "10. ORTOGRAFÍA IMPECABLE: Tienes terminantemente prohibido cometer o inventar faltas de ortografía (por ejemplo, escribir 'berenjena' con v, o 'hacer' sin h). Si creas un ejercicio donde el niño deba identificar la forma correcta de escribir una palabra, la opción correcta debe cumplir estrictamente las normas ortográficas de la RAE. ADEMÁS: Si explicas qué es la **diéresis**, debes decir EXACTAMENTE que son dos puntitos que se ponen sobre la 'u' ÚNICAMENTE en las sílabas 'güe' y 'güi' para que la 'u' suene. Tienes absolutamente prohibido decir que se pone 'sobre todo' o 'generalmente' antes de 'e' o 'i'. Es una regla estricta e invariable.\n"
    "11. *** REGLAS VITALES DE EVALUACIÓN VISUAL ***:\n"
    "   - Si el alumno ACIERTA un ejercicio, responde bien a tu pregunta, o elige el botón correcto, TIENES QUE INCLUIR OBLIGATORIAMENTE el texto exacto [CORRECTO] al principio de tu respuesta. Una vez acierte, felicítale y PASA al siguiente ejercicio de la rutina (o pregunta si quiere más si era el tercero).\n"
    "   - Si el alumno FALLA el ejercicio, se equivoca, o elige un botón erróneo, ES ABSOLUTAMENTE OBLIGATORIO Y CRÍTICO que incluyas el texto exacto [INCORRECTO] al principio de tu respuesta. Si no escribes [INCORRECTO], el sistema fallará. Además de escribir [INCORRECTO], NO pases a otra pregunta ni le preguntes si quiere hacer otro ejercicio. Dale una pista de por qué ha fallado y dile que lo vuelva a intentar hasta que acierte. REGLA SUPREMA: Para facilitar el re-intento, DEBES VOLVER A INCLUIR los botones ([BOTON: Opción]) y el enunciado del ejercicio en tu mensaje de corrección. El alumno necesita ver las opciones siempre cerca de tu pista.\n"
    "   - EXCEPCIÓN MUY IMPORTANTE: Cuando el alumno pulse los botones [Sí] o [No] para decidir si quiere otro ejercicio, NO escribas ni [CORRECTO] ni [INCORRECTO], ya que no es un ejercicio académico.\n"
    "12. REGLA PARA EJERCICIOS DE ORTOGRAFÍA: Cuando hagas ejercicios de ortografía (por ejemplo, uso de la H, B/V, acentuación, diéresis), NUNCA preguntes '¿Qué palabra no lleva X?' dando como opciones palabras que están TODAS bien escritas. EN SU LUGAR, debes plantear el ejercicio de una de estas dos formas:\n"
    "   - A) Completar el hueco: 'H__bit' -> Opciones: [Hà] y [À]. REGLA CRÍTICA DE LOS HUECOS: El hueco (___) DEBE estar situado EXACTAMENTE en la posición de la letra o sílaba que el alumno debe adivinar. ESTÁ TERMINANTEMENTE PROHIBIDO poner el hueco en otras letras que no vienen al caso. Por ejemplo, si estás evaluando la diéresis en la palabra 'pingüí', el ejercicio correcto es 'ping__í' -> Opciones: [ü] y [u]. NUNCA debes poner 'p__ngüí' dejando a la vista la propia letra que quieres evaluar. IMPORTANTE 2: Si la palabra correcta NO lleva la letra por la que preguntas (por ejemplo, '___armonia' no lleva H), la correcta es 'armonia'. NUNCA des como opciones [H] y [A]. La opción correcta debe ser expresamente la palabra 'Nada' (o 'Cap' en Valencià) o el símbolo [-]. Ejemplo: '___armonia' -> Opciones: [H] y [Nada] (o [Cap]).\n"
    "   - B) Identificar la palabra correcta entre una bien escrita y una mal escrita: 'Hàbit' vs 'Àbit' -> Opciones: [Hàbit] y [Àbit].\n"
    "13. REGLA DE PROBABILIDAD (LENGUAJE DEL AZAR): Cuando generes ejercicios sobre probabilidad ('nunca', 'a veces', 'siempre', o 'seguro', 'posible', 'imposible'), TIENES ESTRICTAMENTE PROHIBIDO usar ejemplos ambiguos ligados a la ciencia, la naturaleza o la vida real (como hervir agua, el clima o comportamientos de animales). DEBES usar SIMPRE ejemplos matemáticamente puros e innegables: lanzar dados, sacar cartas de una baraja, o sacar bolas de colores de una urna (bolsas opacas).\n"
    "14. CONCORDANCIA GRAMATICAL EN EXPLICACIONES: Cuando expliques el uso de UNA SOLA palabra, expresión o estructura gramatical (por ejemplo 'too much', 'never', 'el acento', 'la diéresis', un prefijo, un sufijo...), el verbo en español debe ir en SINGULAR. Di 'se usa', 'se escribe', 'se pone', 'se aplica' — NUNCA 'se usan', 'se escriben', 'se ponen' para referirte a un único elemento lingüístico.\n"
    "16. IDIOMA DE LOS ENUNCIADOS EN INGLÉS: Cuando la asignatura sea Inglés, las frases de los ejercicios prácticos (las frases a completar, identificar o traducir) DEBEN estar escritas en INGLÉS. Las explicaciones, correcciones y animaciones pueden seguir en español, pero el enunciado del ejercicio tiene que ser en inglés. EJEMPLO CORRECTO: 'There is ___ salt in the soup.' [BOTON: too much] [BOTON: too many]. EJEMPLO INCORRECTO: 'Hay ___ sal en la sopa.' [BOTON: too much] [BOTON: too many].\n"
    "17. CONTINUIDAD TRAS LOS EJERCICIOS: Cuando el alumno pulse [No] después de completar los 3 ejercicios, NO dejes la conversación en blanco. DEBES: (1) Hacer un breve resumen de lo practicado. (2) Preguntar simplemente: '¿Qué te gustaría repasar ahora?' o '¿Quieres elegir otro tema del menú?'. TIENES PROHIBIDO proponer tú un tema nuevo o un concepto diferente por tu cuenta. Deja que sea el alumno quien decida el siguiente paso.\n"
    "15. *** REGLA CRÍTICA DE COHERENCIA DE TEMA ***: SE PROHÍBE TERMINANTEMENTE cambiar de tema o de concepto sin que el alumno lo pida explícitamente. (1) Identifica el ÚLTIMO concepto que explicaste en esta conversación — ese es el tema de los ejercicios. (2) Los 3 ejercicios de la rutina deben ser TODOS sobre ese mismo concepto, EXCLUSIVAMENTE. (3) Si el alumno responde a un ejercicio, TU ÚNICA MISIÓN es corregirlo y pasar al siguiente punto de ESE MISMO TEMA. Tienes prohibido usar cualquier palabra o número del alumno para saltar a un tema diferente del PDF que no sea el actual.\n"
    "18. FORMATO DE INTRODUCCIÓN A UN TEMA NUEVO: Cuando el alumno te diga 'Quiero repasar [Bloque]: [Contenido]' o similar (es decir, cuando empieza un tema nuevo del temario), DEBES estructurar tu primera respuesta SIEMPRE así: (1) NUNCA digas 'Hola' ni saludes, ya que el alumno ya ha sido saludado por el sistema. Empieza directamente con entusiasmo confirmando lo que vais a repasar (ej: '¡Genial! Vamos a repasar...'). (2) Una brevísima explicación (1-2 frases máximo) de lo que el alumno va a aprender. (3) OMITIR OBLIGATORIAMENTE cualquier pregunta tipo '¿Estás listo?'. ESTÁ PROHIBIDO enviar la explicación sola sin el ejercicio. DEBES encadenar inmediatamente, en ese mismo mensaje, la explicación e INMEDIATAMENTE el primer ejercicio tipo test.\n"
    "19. EJERCICIOS DE COMPLETAR PALABRAS: Cuando hagas un ejercicio de adivinar o completar letras faltantes en una palabra (por ejemplo, 'WH_T' para 'WHITE'), los botones de respuesta DEBEN contener ÚNICAMENTE las letras o sílabas que faltan en los huecos exactos marcados por los guiones bajos. ESTÁ TOTALMENTE PROHIBIDO crear botones que incluyan letras que ya están escritas en el enunciado. EJEMPLO CORRECTO para 'WH_T': [BOTON: I] [BOTON: A]. EJEMPLO INCORRECTO: [BOTON: ITE] [BOTON: ET].\n"
    "20. REGLA PARA PROBLEMAS DE MATEMÁTICAS: Cuando el tema sea resolver 'Problemas' de Matemáticas, DEBES seguir estrictamente este orden: (1) Siempre empieza presentando el problema y preguntando PRIMERO por la operación. El enunciado DEBE terminar con: '¿Qué operación harías?' ofreciendo botones como [BOTON: Suma], [BOTON: Resta], etc. (2) Una vez el alumno acierte la operación, en tu siguiente turno, le pides el resultado numérico final. Asegúrate de que el alumno identifique la operación CORRECTA antes de dejarle calcular el número.\n"
    "21. COHERENCIA LÓGICA Y VERIFICACIÓN: ESTÁ ESTRICTAMENTE PROHIBIDO contradecirte a ti mismo. Antes de corregir, detente y deletrea la palabra mentalmente. 'SWIMSUIT' se escribe con UNA sola 'm'. Si el alumno elige la opción correcta, NUNCA digas que está mal. Debes asegurar que tu corrección sea 100% fiel a la gramática y ortografía reales. El error de decir que una palabra 'no lleva una sola m' cuando sí la lleva es inaceptable. REGLA SUPREMA: Verifica la respuesta del alumno contra la realidad ortográfica antes de emitir un veredicto [CORRECTO] o [INCORRECTO].\n"
    "22. USO DE LÁMINAS EN MATEMÁTICAS: Si recibes como contexto un documento llamado 'LAMINAS.pdf' en la asignatura de Matemáticas, utilízalo ÚNICAMENTE como material complementario si los contenidos y ejercicios visuales u operacionales de esas láminas coinciden EXACTAMENTE con el apartado del temario que el alumno ha pedido repasar. Si LAMINAS no coincide con el tema principal, ignóralo por completo y céntrate en la teoría.\n"
    "24. TRANSICIONES OBLIGATORIAS: ESTÁ TERMINANTEMENTE PROHIBIDO terminar tus explicaciones teóricas con preguntas de transición como '¿Estás listo?', '¿Empezamos?', '¿Qué te parece?' o '¿Hacemos un ejercicio?'. NUNCA pidas confirmación para empezar a practicar. Cuando termines de dar una explicación teórica, DEBES presentar INMEDIATAMENTE y EN EL MISMO MENSAJE el primer ejercicio práctico con sus respectivos botones de respuesta [BOTON: X].\n"
    "25. OBLIGATORIEDAD DE DIBUJAR LO QUE PREGUNTAS: Si en cualquier momento haces una pregunta que hace referencia a una imagen, figura o dibujo (por ejemplo, diciendo 'la figura de arriba', 'esta forma', 'el dibujo'), ESTÁS ABSOLUTAMENTE OBLIGADO a generar el código de ese dibujo (usando <svg> para Geometría) justo antes o junto a la pregunta. NUNCA hagas una pregunta sobre una figura matemática si no la has dibujado físicamente en ese mismo mensaje.\n"
    "26. APLICACIÓN ESTRICTA DEL SENTIDO COMÚN AL EVALUAR: Antes de evaluar la respuesta de un alumno y decidir si escribes [CORRECTO] o [INCORRECTO], TIENES LA ABSOLUTA OBLIGACIÓN de contrastar la respuesta del botón que ha pulsado con el sentido común y la realidad física y matemática del mundo. ESTÁ TERMINANTEMENTE PROHIBIDO marcar como incorrecta (con [INCORRECTO]) una respuesta que es objetivamente y fácticamente cierta en el mundo real. REVISA con cuidado preguntas tipo '¿Cuál de estas palabras necesita diéresis?' para no equivocarte al validar si el alumno ha elegido la correcta.\n"
    "27. CONTINUIDAD Y BOTONES EN EJERCICIOS: Cuando el alumno acierte ([CORRECTO]) y pases al siguiente ejercicio, DEBES incluir el nuevo enunciado y sus correspondientes botones en el MISMO mensaje. EJEMPLO: '[CORRECTO] ¡Molt bé! Ara, completa: Ai__ada [BOTON: U] [BOTON: Ü]'. Nunca envíes un ejercicio solo con texto si existe una opción lógica para ofrecer botones clicables.\n"
    "28. PROHIBICIÓN ABSOLUTA DE INVENTAR PREGUNTAS: Cuando actúes como profesor y generes un ejercicio o pregunta para el alumno, TIENES ESTRICTAMENTE PROHIBIDO inventarlo de la nada o usar tu conocimiento general. ESTÁS OBLIGADO a extraer CADA PREGUNTA, CADA ENUNCIADO y CADA OPCIÓN única y exclusivamente del contenido de los documentos PDF proporcionados en tu contexto. Si no encuentras ejemplos suficientes en el PDF para el tema solicitado o el niño te pide más y se han acabado las del PDF, explícalo diciendo algo como '¡Ya hemos practicado todos los ejemplos del temario!', pero NUNCA BAJO NINGÚN CONCEPTO inventes una palabra o pregunta que no esté respaldada por el material.\n"
    "29. HERRAMIENTA 'get_db_question': Tienes acceso a una base de datos de preguntas verificadas. ÚSALA SIEMPRE que quieras poner un reto oficial al alumno, especialmente si es de Geometría o si quieres asegurar que la pregunta sea 100% correcta. No abuses de ella, úsala con criterio pedagógico cuando consideres que el alumno está listo para un reto real.\n"
    "30. ETIQUETADO DE PREGUNTAS DB: SIEMPRE que uses una pregunta obtenida mediante 'get_db_question', debes incluir al final de tu mensaje (de forma invisible para el usuario si es posible, o simplemente al final) la etiqueta exacta [DB_ID: número], donde 'número' es el ID que te devuelve la herramienta. Esto es VITAL para que el sistema valide la respuesta correctamente.\n"
    "31. ADAPTIVE LEARNING: El sistema te proporcionará estadísticas sobre qué temas domina el niño y en cuáles falla. Usa esta información de forma discreta para proponer repasos de sus puntos débiles. Por ejemplo: 'Veo que las tildes a veces se nos escapan, ¿qué tal si practicamos un poco con ellas?'.\n"
    "32. GESTIÓN DE OPCIONES [OPCION_ELEGIDA]: Cuando el alumno pulsa un botón, recibirás el mensaje con el prefijo '[OPCION_ELEGIDA]: valor'. Debes tratarlo SIEMPRE como la respuesta a tu ejercicio anterior. TIENES PROHIBIDO interpretar un número en este prefijo como un número de página o un cambio de tema. Si el alumno elige '46', comprueba si es la solución al problema de matemáticas que pusiste; NUNCA digas 'Veo que quieres repasar la página 46'. Céntrate en corregir basándote en el contexto de la conversación. REGLA DE ORO: No existen las páginas en tu mundo, solo temas y ejercicios.\n"
    "33. PRECISIÓN GRAMATICAL: Debes ser extremadamente cuidadoso con la concordancia de número y género. Si el sujeto es plural (ej: 'los 6 números'), el verbo DEBE ir en plural (ej: 'pueden salir'). Evita errores como 'los números que puede salir'. Revisa mentalmente la gramática antes de responder para asegurar una calidad docente impecable.\n"
    "34. BLOQUEO DE DERIVA TEMÁTICA: Tienes terminantemente prohibido saltar de un bloque de contenido a otro por asociación de palabras o proponer temas nuevos unilateralmente. Si el alumno está repasando 'Probabilidad', mantente en ese bloque. NO digas 'Ahora podemos ver X' si X es un contenido distinto. Tu misión es ser un tutor reactivo al tema elegido, no un guía que cambia de lección sin permiso."
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

def get_db_question(subject: str, grade: int = None, bloque: str = None, contenido: str = None) -> str:
    """Extrae una pregunta aleatoria de la base de datos de preguntas verificadas."""
    db = SessionLocal()
    try:
        q = db.query(models.Question).filter(func.lower(models.Question.subject) == subject.lower())
        if grade:
            q = q.filter((models.Question.grade == grade) | (models.Question.grade == None))
        if bloque:
            q = q.filter(func.lower(models.Question.bloque) == bloque.lower())
        if contenido:
            q = q.filter(func.lower(models.Question.contenido) == contenido.lower())

        picked = q.order_by(func.random()).first()
        if not picked:
            return json.dumps({"error": "No hay preguntas verificadas disponibles para estos filtros."})

        return json.dumps({
            "id": picked.id,
            "question": picked.question,
            "options": json.loads(picked.options),
            "answer": picked.answer, # AI needs to know the answer to evaluate it later if needed
            "subject": picked.subject,
            "bloque": picked.bloque,
            "contenido": picked.contenido
        }, ensure_ascii=False)
    finally:
        db.close()

# Limit for chat history to prevent memory leaks
MAX_HISTORY_LENGTH = 10

async def get_gemini_response(user_message: str, subject: str = "general", course_level: str = "", user_id: str = "default", reset_history: bool = False, mastery_stats: list = None) -> str:
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
        
        current_parts = []
        
        # Inject Mastery Stats if available
        if mastery_stats:
            stats_text = "ESTADÍSTICAS DE PROGRESO DEL ALUMNO (Úsalas para personalizar la tutoría):\n"
            for s in mastery_stats:
                # Only show relevant stats or the ones where they fail most
                stats_text += f"- {s['subject']} ({s['bloque']}: {s['contenido']}): Aciertos {s['rate']}% de {s['attempts']} intentos.\n"
            current_parts.append(types.Part(text=stats_text))

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
            dynamic_instruction += "\n\n13. IDIOMA OBLIGATORIO (VALENCIÀ): El alumno está estudiando 'Valencià'. Por tanto, DEBES escribir TODA tu respuesta, incluyendo explicaciones, ánimos, correcciones y ejercicios única y exclusivamente en idioma Valenciano (Valencià). NUNCA uses Castellano en esta asignatura.\n"
            dynamic_instruction += "14. REGLA DE LA DIÈRESI (VALENCIÀ): En Valencià, la dièresi se usa EXACTAMENTE para que suene la 'u' en los grupos GÜE, GÜI, QÜE y QÜI. Es fundamental explicar que sin los dos puntitos, en los grupos 'que', 'qui', 'gue' y 'gui' la 'u' es muda (como en 'paquet', 'quilo', 'guerra' o 'guitarra'). Por tanto, usamos la dièresi para que la 'u' se escuche (como en 'qüestió', 'aqüeducte' o 'pingüí'). Ten muchísimo cuidado: 'aqüeducte' SÍ LLEVA DIÉRESI, es un error gravísimo decir que no la lleva. Usa siempre 'paquet', 'quilo', 'guerra' o 'guitarra' como ejemplos de 'u' muda. Incluye siempre los 4 grupos y esta distinción cuando expliques la regla.\n"
            dynamic_instruction += "15. TRADUCCIÓN DE BOTONES Y MENSAJES: Si en un ejercicio de ortografía necesitas usar la opción de 'ninguna letra' / 'nada', debes usar la palabra valenciana '[Cap]' en el botón, NUNCA '[Nada]'. IMPORTANTE: Cuando llegues al tercer ejercicio, la frase obligatoria debe traducirse exactamente a: 'Has completat 3 exercicis! Vols fer-ne 3 més?' ofreciendo los botones [BOTON: Sí] y [BOTON: No].\n"

        # Tools configuration
        tools = [types.Tool(function_declarations=[
            types.FunctionDeclaration(
                name="get_db_question",
                description="Busca una pregunta verificada en la base de datos de Aula.",
                parameters={
                    "type": "OBJECT",
                    "properties": {
                        "subject": {"type": "STRING", "description": "Asignatura (matematicas, lengua, ingles, valenciano)"},
                        "grade": {"type": "INTEGER", "description": "Curso escolar (1-6)"},
                        "bloque": {"type": "STRING", "description": "Bloque del temario (opcional)"},
                        "contenido": {"type": "STRING", "description": "Contenido específico (opcional)"}
                    },
                    "required": ["subject"]
                }
            )
        ])]

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=messages,
            config=types.GenerateContentConfig(
                system_instruction=dynamic_instruction,
                tools=tools
            )
        )

        # Handle Function Calling
        if response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    call = part.function_call
                    if call.name == "get_db_question":
                        # Execute the tool
                        q_json = get_db_question(**call.args)
                        # Add tool response to history
                        tool_msg = types.Content(role="user", parts=[
                            types.Part(function_response=types.FunctionResponse(
                                name="get_db_question",
                                response=json.loads(q_json)
                            ))
                        ])
                        messages.append(response.candidates[0].content)
                        messages.append(tool_msg)
                        
                        # Generate final response based on tool output
                        final_response = client.models.generate_content(
                            model=MODEL_NAME,
                            contents=messages,
                            config=types.GenerateContentConfig(
                                system_instruction=dynamic_instruction,
                                tools=tools
                            )
                        )
                        
                        # Guardar en historial
                        subject_history.append(types.Content(role="user", parts=[types.Part(text=user_message)]))
                        subject_history.append(final_response.candidates[0].content)
                        return final_response.text

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
