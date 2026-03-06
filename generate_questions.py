#!/usr/bin/env python3
"""
generate_questions.py — Batch question generator for AulaRAG.

Usage:
  # Generate 15 questions for Lengua, Grade 3, Ortografía topic "Uso de la H"
  python generate_questions.py --subject lengua --grade 3 --bloque Ortografía --contenido "Uso de la H" --num 15

  # Import a previously generated JSON file into the DB (server must NOT be running, or use admin API)
  python generate_questions.py --import questions_lengua_g3.json

  # Import via the admin API (server must be running)
  python generate_questions.py --api-import questions_lengua_g3.json --url http://localhost:8000 --token YOUR_JWT_TOKEN
"""

import argparse
import json
import os
import sys
import re

import requests


def _get_cached_gemini_uri(subject: str, grade: int | None) -> str | None:
    """Find the cached Gemini URI for a given subject and grade from the server's cache."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cache_file = os.path.join(base_dir, "data", "gemini_file_cache.json")
    
    if not os.path.exists(cache_file) or grade is None:
        return None

    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            cache = json.load(f)
    except Exception:
        return None

    grade_padded = str(grade).zfill(2)  # "03"

    candidates = []
    if subject.lower() == "matematicas":
        candidates.append(f"{subject.lower()}_Aula_Matematicas_{grade_padded}_INTERIOR.pdf")
    elif subject.lower() == "lengua":
        candidates.append(f"{subject.lower()}_Aula_Lengua_{grade_padded}.pdf")
    elif subject.lower() == "valenciano":
        candidates.append(f"{subject.lower()}_AULA_VALENCIANO_{grade}.pdf")
    elif subject.lower() == "ingles":
        candidates.append(f"{subject.lower()}_Aula_english_{grade_padded}.pdf")
        candidates.append(f"{subject.lower()}_Aula_english_{grade_padded}_Part1.pdf")
    else:
        candidates.append(f"{subject.lower()}_Aula_{subject.capitalize()}_{grade_padded}_INTERIOR.pdf")

    for name in candidates:
        if name in cache:
            return cache[name]

    return None

def _find_pdf_for_subject(subject: str, grade: int | None) -> str | None:
    """Find the local plain text fallback if any."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    source_dir = os.path.join(base_dir, "data", "source_files", subject.lower())
    
    if grade is None:
        return None
    grade_padded = str(grade).zfill(2)
    txt = os.path.join(source_dir, f"Aula_{subject.lower()}_{grade_padded}.txt")
    if os.path.exists(txt):
        return txt
    return None

def generate_via_gemini(subject: str, grade: int | None, bloque: str | None, contenido: str | list | None, num: int) -> list[dict]:
    """Call Gemini to generate a batch of questions, optionally grounded in the subject PDF."""
    try:
        from google import genai
        from google.genai import types as genai_types
        from dotenv import load_dotenv
        load_dotenv()
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    except ImportError:
        print("ERROR: google-genai package not installed. Run: pip install google-genai")
        sys.exit(1)
    except KeyError:
        print("ERROR: GEMINI_API_KEY environment variable not set.")
        sys.exit(1)

    grade_str = f"de {grade}º de Primaria" if grade else "de Educación Primaria"
    bloque_str = f"Bloque: {bloque}" if bloque else ""
    if isinstance(contenido, list):
        contenido_str = f"Contenidos a repartir equitativamente: {', '.join(contenido)}"
    else:
        contenido_str = f"Contenido concreto: {contenido}" if contenido else ""

    # Try to find and upload the PDF for this subject+grade
    contents = []
    
    cached_uri = _get_cached_gemini_uri(subject, grade)
    
    # Logic to find the local PDF path for re-upload if needed
    base_dir = os.path.dirname(os.path.abspath(__file__))
    source_dir = os.path.join(base_dir, "data", "source_files", subject.lower())
    local_pdf = None
    if grade:
        grade_padded = str(grade).zfill(2)
        if subject.lower() == "matematicas":
            local_pdf = os.path.join(source_dir, f"Aula_Matematicas_{grade_padded}_INTERIOR.pdf")
        elif subject.lower() == "lengua":
            local_pdf = os.path.join(source_dir, f"Aula_Lengua_{grade_padded}.pdf") # Adjust if needed
        elif subject.lower() == "valenciano":
            local_pdf = os.path.join(source_dir, f"AULA_VALENCIANO_{grade}.pdf")
        elif subject.lower() == "ingles":
            local_pdf = os.path.join(source_dir, f"Aula_english_{grade_padded}.pdf")

    has_context = False
    
    # Helper to upload/re-upload
    def upload_file(path):
        print(f"Uploading {os.path.basename(path)} to Gemini...")
        uploaded = client.files.upload(path=path)
        # Update cache in memory/file if possible, but at least return uri
        cache_file = os.path.join(base_dir, "data", "gemini_file_cache.json")
        try:
            with open(cache_file, "r") as f: cache = json.load(f)
            # Find the key that matches this file
            for k in cache:
                if os.path.basename(path) in k:
                    cache[k] = uploaded.uri
                    break
            else:
                cache[f"{subject.lower()}_{os.path.basename(path)}"] = uploaded.uri
            with open(cache_file, "w") as f: json.dump(cache, f, indent=2)
        except: pass
        return uploaded.uri

    if cached_uri:
        # We wrap in a try/except for the actual generation later, 
        # but let's see if we can proactively verify or just prepare a fallback
        contents.append(genai_types.Part(
            file_data=genai_types.FileData(file_uri=cached_uri, mime_type="application/pdf")
        ))
        has_context = True
    elif local_pdf and os.path.exists(local_pdf):
        new_uri = upload_file(local_pdf)
        contents.append(genai_types.Part(
            file_data=genai_types.FileData(file_uri=new_uri, mime_type="application/pdf")
        ))
        has_context = True
    else:
        txt_path = _find_pdf_for_subject(subject, grade)
        if txt_path and txt_path.endswith(".txt"):
            print(f"📄 Usando texto local como fuente: {os.path.basename(txt_path)}")
            with open(txt_path, "r", encoding="utf-8") as f:
                text_content = f.read()
            contents.append(genai_types.Part(text=f"CONTENIDO DEL LIBRO:\n{text_content}"))
            has_context = True
        else:
            print(f"⚠️  No se encontró caché en Gemini ni txt local ni PDF original para {subject} grado {grade}.")
            print(f"Generando desde conocimiento general de la IA.")

    # ... prompt ...

    prompt = f"""Eres un experto generador de preguntas de test para Educación Primaria española.
Genera exactamente {num} preguntas de tipo test para la asignatura de {subject.capitalize()} {grade_str}.
{bloque_str}
{contenido_str}

{"Basa las preguntas EXCLUSIVAMENTE en el documento adjunto. Las preguntas deben referirse a conceptos, reglas o ejemplos que aparezcan directamente en ese material." if has_context else ""}

INSTRUCCIONES MUY IMPORTANTES:
1. Cada pregunta debe tener EXACTAMENTE 3 opciones de respuesta.
2. UNA Y SÓLO UNA opción debe ser la correcta. Las otras deben ser claramente incorrectas.
3. Las preguntas deben ser claras y adecuadas para niños de Primaria.
4. JAMÁS incluyas opciones donde ninguna sea correcta, o donde varias lo sean.
5. Responde ÚNICAMENTE con un JSON válido, sin ningún texto antes ni después.
6. DEBES INCLUIR LA CLAVE 'contenido' EN CADA OBJETO JSON con el nombre exacto del contenido al que pertenece la pregunta.

Formato de respuesta (array JSON):
[
  {{
    "question": "Texto de la pregunta",
    "options": ["Opción A", "Opción B", "Opción C"],
    "answer": "Opción A",
    "contenido": "Nombre del contenido exacto"
  }},
  ...
]
"""

    contents.append(genai_types.Part(text=prompt))

    print(f"🤖 Preparando prompt para Gemini...")

    try:
        try:
            response = client.models.generate_content(
                model="gemini-flash-latest", # Switching to stable alias
                contents=contents,
            )
        except Exception as e:
            if "403" in str(e) and local_pdf and os.path.exists(local_pdf):
                print(f"⚠️ URI expirada o sin permisos. Intentando re-subir {os.path.basename(local_pdf)}...")
                new_uri = upload_file(local_pdf)
                # Swap the Part
                for i, p in enumerate(contents):
                    if p.file_data:
                        contents[i] = genai_types.Part(
                            file_data=genai_types.FileData(file_uri=new_uri, mime_type="application/pdf")
                        )
                response = client.models.generate_content(
                    model="gemini-flash-latest",
                    contents=contents,
                )
            else:
                raise e
        print("✅ Respuesta recibida de Gemini.")

    except Exception as api_err:
        print(f"❌ Error en la API de Gemini: {api_err}")
        raise
    raw = response.text.strip()


    # Strip markdown code blocks if present
    raw = re.sub(r'^```json\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)

    questions = json.loads(raw)

    # Enrich with metadata
    for q in questions:
        q["subject"] = subject.lower()
        if grade:
            q["grade"] = grade
        if bloque:
            q["bloque"] = bloque
        if not isinstance(contenido, list) and contenido and "contenido" not in q:
            q["contenido"] = contenido
        # If it's a list, the AI should have added 'contenido'. Fallback to first if missing.
        elif isinstance(contenido, list) and "contenido" not in q:
            q["contenido"] = contenido[0]

    return questions




def import_to_db_direct(questions: list[dict], db_path: str):
    """Import questions directly into SQLite using SQLAlchemy (server must be stopped)."""
    import json as _json
    from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
    from sqlalchemy.orm import sessionmaker, declarative_base
    from datetime import datetime

    Base = declarative_base()

    class Question(Base):
        __tablename__ = "questions"
        id = Column(Integer, primary_key=True)
        subject = Column(String)
        grade = Column(Integer, nullable=True)
        bloque = Column(String, nullable=True)
        contenido = Column(String, nullable=True)
        question = Column(Text)
        options = Column(Text)
        answer = Column(String)
        created_at = Column(DateTime, default=datetime.utcnow)

    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    count = 0
    for item in questions:
        q = Question(
            subject=item["subject"],
            grade=item.get("grade"),
            bloque=item.get("bloque"),
            contenido=item.get("contenido"),
            question=item["question"],
            options=_json.dumps(item["options"], ensure_ascii=False),
            answer=item["answer"],
        )
        session.add(q)
        count += 1
    session.commit()
    session.close()
    print(f"✅ {count} preguntas importadas directamente a la BD.")


def import_via_api(questions: list[dict], base_url: str, token: str):
    """Import questions via the /admin/questions API endpoint."""
    url = f"{base_url.rstrip('/')}/admin/questions"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.post(url, json=questions, headers=headers)
    if response.ok:
        data = response.json()
        print(f"✅ {data.get('created', '?')} preguntas importadas vía API.")
    else:
        print(f"❌ Error al importar: {response.status_code} — {response.text}")


def main():
    parser = argparse.ArgumentParser(description="AulaRAG Question Bank Generator")
    parser.add_argument("--subject",   help="Asignatura: lengua, matematicas, valenciano, ingles")
    parser.add_argument("--grade",     type=int, help="Curso: 1-6")
    parser.add_argument("--bloque",    help="Bloque del temario (ej: Ortografía)")
    parser.add_argument("--contenido", help="Contenido concreto (ej: Uso de la H)")
    parser.add_argument("--num",       type=int, default=10, help="Número de preguntas a generar")
    parser.add_argument("--output",    help="Fichero JSON de salida (por defecto: auto-generated name)")
    parser.add_argument("--import",    dest="import_file", help="Importar directamente un fichero JSON a la BD")
    parser.add_argument("--api-import",dest="api_import",  help="Importar vía la API REST del servidor")
    parser.add_argument("--url",       default="http://localhost:8000", help="URL del servidor")
    parser.add_argument("--token",     help="JWT token de administrador para importar vía API")

    args = parser.parse_args()

    # --- Direct DB import mode ---
    if args.import_file:
        with open(args.import_file, encoding="utf-8") as f:
            questions = json.load(f)
        db_path = os.path.join(os.path.dirname(__file__), "data", "aula_rag.db")
        import_to_db_direct(questions, db_path)
        return

    # --- API import mode ---
    if args.api_import:
        if not args.token:
            print("ERROR: Necesitas --token para importar vía API.")
            sys.exit(1)
        with open(args.api_import, encoding="utf-8") as f:
            questions = json.load(f)
        import_via_api(questions, args.url, args.token)
        return

    # --- Generation mode ---
    if not args.subject:
        parser.print_help()
        sys.exit(1)

    print(f"🤖 Generando {args.num} preguntas para {args.subject} (Curso {args.grade or 'todos'}, Bloque: {args.bloque or 'todos'}, Contenido: {args.contenido or 'todos'})...")
    questions = generate_via_gemini(args.subject, args.grade, args.bloque, args.contenido, args.num)

    # Output file name
    parts = [args.subject]
    if args.grade:
        parts.append(f"g{args.grade}")
    if args.bloque:
        parts.append(args.bloque.lower().replace(" ", "_"))
    if args.contenido:
        parts.append(args.contenido.lower().replace(" ", "_")[:20])
    out_file = args.output or f"questions_{'_'.join(parts)}.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(questions)} preguntas guardadas en: {out_file}")
    print(f"\n👇 Revisa el fichero y luego impórtalo así:")
    print(f"   python generate_questions.py --import {out_file}")


if __name__ == "__main__":
    main()
