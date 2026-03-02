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
    "4. USO DE LOS LIBROS: Utiliza siempre la información de los libros de texto adjuntos para anclar tus explicaciones en lo que está estudiando. Sin embargo, NUNCA menciones al alumno que estás sacando la información de un libro o de un PDF, y NUNCA le digas de qué página es el ejercicio.\n"
    "5. FORMATO AMIGABLE: Sé muy conciso. Usa párrafos cortos (máximo 2 o 3 líneas) y negritas para destacar palabras importantes. En tu primera respuesta a una nueva pregunta, utiliza un máximo de 60 palabras de forma muy directa y al grano.\n"
    "6. ROL: Eres un profesor virtual; si el alumno pregunta cosas fuera del entorno escolar, reconduce la conversación hacia los estudios de forma neutral.\n"
    "7. MINIJUEGOS Y BOTONES: Cuando quieras hacerle una pregunta interactiva tipo test al alumno, pon cada opción dentro de esta sintaxis: [BOTON: Opción]. TAMBIÉN, cuando quieras saber si quiere continuar practicando, pregúntale EXACTAMENTE la frase '¿Quieres otro ejercicio?' y ofrécele SIEMPRE debajo las opciones [BOTON: Sí] y [BOTON: No]. IMPORTANTE: Si el alumno responde 'Sí' a esta pregunta, NO digas '¡Genial! Vamos con otro' ni frases de transición largas: plantea el nuevo ejercicio DIRECTAMENTE en la primera línea.\n"
    "8. VALIDACIÓN DE PREGUNTAS: Antes de enviar un ejercicio tipo test de varias opciones, ASEGÚRATE AL 100% de que una (y solo una) de las opciones sea verdaderamente correcta, y que el resto de opciones sean TOTALMENTE INCORRECTAS de forma inequívoca. Nunca le des dos posibles respuestas correctas a un niño (por ejemplo, si preguntas por un extranjerismo, no pongas 'pizza' y 'ballet' a la vez). Nunca le des opciones donde todas sean falsas o imposibles de resolver. PROHIBIDO generar ejercicios de completar letras si no incluyes exactamente la letra correcta que falta dentro de uno de los botones.\n"
    "9. *** REGLAS VITALES DE EVALUACIÓN VISUAL ***:\n"
    "   - Si el alumno ACIERTA un ejercicio, responde bien a tu pregunta, o elige el botón correcto, TIENES QUE INCLUIR OBLIGATORIAMENTE el texto exacto [CORRECTO] en tu respuesta.\n"
    "   - Si el alumno FALLA el ejercicio, se equivoca, o elige un botón erróneo, TIENES QUE INCLUIR OBLIGATORIAMENTE el texto exacto [INCORRECTO] en tu respuesta. Además, MUY IMPORTANTE: NO pases a otra pregunta ni le preguntes si quiere hacer otro ejercicio. Dale una pista de por qué ha fallado y dile que lo vuelva a intentar hasta que acierte.\n"
    "   - EXCEPCIÓN MUY IMPORTANTE: Cuando el alumno pulse los botones [Sí] o [No] para decidir si quiere otro ejercicio, NO escribas ni [CORRECTO] ni [INCORRECTO], ya que no es un ejercicio académico.\n"
    "   ¡El sistema visual se romperá si no escribes [CORRECTO] o [INCORRECTO] cuando corrijas algo!"
)

# Chat history kept in memory (per-server-process)
chat_history = []
existing_files_cache = {}

def load_pdf_files_as_parts():
    """Scans the subject folders and uploads any new PDFs. Populates existing_files_cache."""
    global existing_files_cache
    source_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "source_files")
    
    if not os.path.exists(source_dir) or not client:
        return

    # Fetch already uploaded files from Gemini to prevent duplicates
    print("Checking Gemini for already uploaded files...")
    try:
        for f in client.files.list():
            existing_files_cache[f.display_name] = f
    except Exception as e:
        print(f"Failed to list existing files: {e}")

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
                    except Exception as e:
                        print(f"  -> Failed to upload {filename}: {e}")

def get_pdf_part_for_context(subject: str, course_level: str):
    """Returns the specific Gemini file part for the requested subject and course, using the cache."""
    if not course_level:
        return None
        
    grade_match = "".join([c for c in course_level if c.isdigit()])
    if not grade_match:
        return None
        
    grade_num = grade_match.zfill(2) # e.g. "03"
    expected_filename = f"Aula_{subject.capitalize()}_{grade_num}_INTERIOR.pdf"
    expected_display_name = f"{subject}_{expected_filename}"
    
    cached_file = existing_files_cache.get(expected_display_name)
    if cached_file:
        return types.Part(file_data=types.FileData(file_uri=cached_file.uri, mime_type="application/pdf"))
    
    return None

# Load PDFs at startup to populate cache
if client:
    load_pdf_files_as_parts()

async def get_gemini_response(user_message: str, subject: str = "general", course_level: str = "") -> str:
    """Sends a message to Gemini using the new SDK and returns the response."""
    if not client:
        return "⚠️ Error: API Key de Gemini no configurada. Por favor, revisa el archivo .env."

    try:
        # Build full conversation with memory history (minus PDFs, which are injected dynamically below)
        messages = list(chat_history)
        
        current_parts = []
        pdf_part = get_pdf_part_for_context(subject, course_level)
        if pdf_part:
            current_parts.append(pdf_part)
            current_parts.append(types.Part(text=f"Este es el cuaderno de actividades de {course_level} de {subject}. Úsalo obligatoriamente para basar tus explicaciones o inventar ejercicios."))
        else:
            current_parts.append(types.Part(text="Responde a la pregunta del alumno de forma general."))
            
        current_parts.append(types.Part(text=user_message))
        
        messages.append(types.Content(role="user", parts=current_parts))

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=messages,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
        )

        # Append to history to maintain conversation context (without the PDF part to save context window space)
        chat_history.append(types.Content(role="user", parts=[types.Part(text=user_message)]))
        chat_history.append(types.Content(role="model", parts=[types.Part(text=response.text)]))

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
        return True
    except Exception as e:
        print(f"Error uploading file: {e}")
        return False
