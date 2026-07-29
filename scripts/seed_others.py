import os
import re
from sqlalchemy.orm import Session
from app import models, database

def parse_lecturas_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by LECTURA X:
    parts = re.split(r'LECTURA \d+:', content)
    stories = []
    for part in parts[1:]:
        lines = part.strip().split('\n')
        title = lines[0].strip()
        
        # Extract content between TEXTO: and PREGUNTAS
        text_match = re.search(r'TEXTO:(.*?)PREGUNTAS', part, re.DOTALL)
        if text_match:
            text = text_match.group(1).strip()
            stories.append({"title": title, "content": text})
    return stories

def seed_all():
    db = database.SessionLocal()
    
    # 1st Grade
    file1 = 'data/source_files/competencia_lectora/lecturas_1_grado_final.txt'
    if os.path.exists(file1):
        stories1 = parse_lecturas_file(file1)
        for s in stories1:
            upsert_story(db, 1, s['title'], s['content'])

    # 2nd Grade
    file2 = 'data/source_files/competencia_lectora/lecturas_2_grado_final.txt'
    if os.path.exists(file2):
        stories2 = parse_lecturas_file(file2)
        for s in stories2:
            upsert_story(db, 2, s['title'], s['content'])
            
    db.commit()
    db.close()

def upsert_story(db, grade, title, content):
    existing = db.query(models.Explanation).filter(
        models.Explanation.subject == "competencia_lectora",
        models.Explanation.contenido == title
    ).first()
    
    if existing:
        existing.text = content
        print(f"Updated {grade}º Grade: {title}")
    else:
        new_exp = models.Explanation(
            subject="competencia_lectora",
            grade=grade,
            bloque="Lecturas",
            contenido=title,
            text=content,
            is_active=True,
            is_verified=True
        )
        db.add(new_exp)
        print(f"Added {grade}º Grade: {title}")

if __name__ == "__main__":
    seed_all()
