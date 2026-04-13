
import sys
import os
sys.path.append(os.getcwd())
from app.rag_engine import get_db_question
import json

# Test cases
subjects = ["matematicas", "matemáticas", "Mates"]
grade = 1
bloque = "Probabilidad"

for s in subjects:
    print(f"\n--- Testing Subject: {s} ---")
    res = get_db_question(s, grade, bloque)
    data = json.loads(res)
    if "error" in data:
        print(f"FAILED: {data['error']}")
    else:
        print(f"SUCCESS: Found question {data['identifier']} (ID {data['id']})")
