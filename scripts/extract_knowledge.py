import os
import sys
import json
import time
from typing import List, Optional
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app import models

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def extract_from_pdf(file_path: str, subject: str, grade: int):
    """Processes a PDF and extracts explanations into the DB."""
    if not client:
        print("Error: GEMINI_API_KEY not found.")
        return

    print(f"--- Processing: {os.path.basename(file_path)} ({subject}, Grade {grade}) ---")
    
    # 1. Upload file to Gemini
    print("Uploading file to Gemini...")
    uploaded_file = client.files.upload(file=file_path)
    
    # Wait for processing
    while uploaded_file.state.name == "PROCESSING":
        print(".", end="", flush=True)
        time.sleep(2)
        uploaded_file = client.files.get(name=uploaded_file.name)
    
    if uploaded_file.state.name == "FAILED":
        print("\nUpload failed.")
        return
    print("\nFile ready.")

    # 2. Ask Gemini to extract data
    prompt = (
        "Eres un experto en currículo escolar español de primaria. Analiza este libro de texto PDF.\n"
        "Tu objetivo es identificar los TEMAS principales (contenido) y escribir una EXPLICACIÓN teórica "
        "impecable, dulce y pedagógica para un niño de ese curso.\n\n"
        "REQUISITOS DEL FORMATO JSON (Devuelve una lista de objetos):\n"
        "- bloque: El bloque curricular (ej: Números, Geometría, Ortografía).\n"
        "- contenido: El nombre específico del tema (ej: La suma sin llevar, La diéresis).\n"
        "- explanation: Una lección completa (2-3 párrafos) explicando el concepto con ejemplos claros.\n\n"
        "RESPONDE ÚNICAMENTE CON EL JSON. NO INCLUYAS EXPLICACIONES EXTRA.\n"
        "Busca al menos 10 temas significativos del libro."
    )

    print("Generating explanations...")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(file_data=types.FileData(file_uri=uploaded_file.uri, mime_type=uploaded_file.mime_type)),
                    types.Part.from_text(text=prompt)
                ]
            )
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )

    try:
        data = json.loads(response.text)
        if not isinstance(data, list):
            # In case it returned a single object or wrapped in another field
            if isinstance(data, dict) and "temas" in data:
                data = data["temas"]
            elif isinstance(data, dict):
                data = [data]
        
        print(f"Found {len(data)} topics. Saving to database...")
        
        db = SessionLocal()
        try:
            for item in data:
                # Check for required fields
                if not all(k in item for k in ["contenido", "explanation"]):
                    continue
                
                # Create or Update
                existing = db.query(models.TopicExplanation).filter(
                    models.TopicExplanation.subject == subject,
                    models.TopicExplanation.grade == grade,
                    models.TopicExplanation.contenido == item["contenido"]
                ).first()
                
                if existing:
                    existing.explanation = item["explanation"]
                    existing.bloque = item.get("bloque", existing.bloque)
                    print(f"  [Update] {item['contenido']}")
                else:
                    new_exp = models.TopicExplanation(
                        subject=subject,
                        grade=grade,
                        bloque=item.get("bloque"),
                        contenido=item["contenido"],
                        explanation=item["explanation"]
                    )
                    db.add(new_exp)
                    print(f"  [Insert] {item['contenido']}")
            
            db.commit()
            print("Successfully updated database.")
        finally:
            db.close()

    except Exception as e:
        print(f"Error parsing or saving data: {e}")
        print("Raw response:", response.text)

if __name__ == "__main__":
    # Example: 1st Grade Mathematics batch
    MATH_G1 = "./data/source_files/matematicas/Aula_Matematicas_01_INTERIOR.pdf"
    if os.path.exists(MATH_G1):
        extract_from_pdf(MATH_G1, "matematicas", 1)
    else:
        print(f"File not found: {MATH_G1}")
