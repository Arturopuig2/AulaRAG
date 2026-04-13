import sys
import os
import re

import asyncio

# Add the project directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.rag_engine import get_gemini_response, clean_ai_text

async def run_test(name, subject, user_input, expected_eval=None):
    print(f"\n--- TEST: {name} ---")
    print(f"Input: {user_input}")
    
    response = await get_gemini_response(user_input, subject)
    print(f"Response:\n{response}")
    
    errors = []
    
    # Rule: Correct evaluation (if specified)
    if expected_eval == "INCORRECTO":
        # Check if response sounds overly positive despite being an error turn
        if any(ok in response.lower() for ok in ["¡excelente!", "¡muy bien!", "¡perfecto!"]):
             # If it doesn't also contain negative signals, it's a false positive
             if "no es correcto" not in response.lower() and "incorrecto" not in response.lower():
                 errors.append("Parece haber validado una respuesta incorrecta (Falso Positivo)")

    # Rule 1: Starts with Explicación: (Every time 'repasar' or a new topic is requested)
    if any(kw in user_input.lower() for kw in ["repasar", "repaso", "tema"]):
        if not response.strip().startswith("Explicación:"):
            errors.append("No empieza con 'Explicación:' a pesar de ser un repaso/tema nuevo")
            
    # Rule 2: No gendered praise
    gendered_terms = ['campeón', 'campeona', 'listo', 'lista', 'niño', 'niña']
    for term in gendered_terms:
        if re.search(r'\b' + term + r'\b', response.lower()):
            errors.append(f"Uso de término con género: '{term}'")
            
    # Rule 3: No quotes for emphasis
    if '"' in response:
        errors.append("Uso de comillas detectada (debería ser negrita)")
        
    # Rule 4: Mandatory spacing after punctuation
    if re.search(r'[.!?,;:][a-zA-ZáéíóúÁÉÍÓÚñÑ]', response):
        errors.append("Falta espacio después de signo de puntuación")
        
    # Rule 5: No conversational intros
    intros = ['claro que sí', 'me encanta', 'qué divertido', '¡hola!', 'empecemos', 'parece que no hay', 'no hay problema', 'puedo crear']
    for intro in intros:
        if intro in response.lower():
             errors.append(f"Mensaje de relleno o intro detectada: '{intro}'")

    # Rule 6: No reasoning/rule leakage
    leak_keywords = ['página', 'pdf', 'libro', 'fuente', 'material', 'revisando', '206', '207', '208']
    for kw in leak_keywords:
        if kw in response.lower():
             errors.append(f"Filtrado de material fallido (leak detectado): '{kw}'")

    if re.search(r'\(\d+\)', response):
        errors.append("Filtrado de reglas fallido (eco de instrucciones detectado)")

    if not errors:
        print("✅ PASSED")
        return True
    else:
        print("❌ FAILED")
        for err in errors:
            print(f"  - {err}")
        return False

async def main():
    success = True
    
    # Test Case 1: New Topic Selection
    success &= await run_test(
        "Nuevo Tema (Matemáticas)", 
        "matemáticas", 
        "Quiero repasar los problemas de sumas sin llevar."
    )
    
    # Test Case 2: Praise / Reinforcement
    success &= await run_test(
        "Refuerzo Positivo", 
        "lengua", 
        "¿He acertado el ejercicio del rey?"
    )

    # Test Case 3: Mandatory Explanation on Repasar
    success &= await run_test(
        "Explicación en Repaso", 
        "lengua", 
        "Quiero repasar: Diptongo, triptongo e hiato"
    )

    # Test Case 4: Evaluation Accuracy (The specific bug fix)
    # We simulate the button click injected message for a math problem
    success &= await run_test(
        "Precisión de Evaluación (Error en Suma)", 
        "matemáticas", 
        "[CORRECTO] [INCORRECTO] El alumno ha pulsado el botón 'Resta' para preguntar qué operación harías para saber cuánto pesan las naranjas (5kg) y las manzanas (11kg) juntas.",
        expected_eval="INCORRECTO"
    )

    # Test Case 5: False Negative / Contradiction Fix (Circle vs Circumference)
    success &= await run_test(
        "Falso Negativo (Círculo vs Circunferencia)",
        "matemáticas",
        "[CORRECTO] [INCORRECTO] El alumno ha pulsado el botón 'Toda la galleta, con su relleno si tiene' para preguntar ¿Qué parte de la galleta redonda sería el círculo?",
        expected_eval="CORRECTO"
    )
    
    # Test Case 6: Source Protection (Rule 38)
    success &= await run_test(
        "Protección de Fuente (Regla 38)",
        "lengua",
        "¿De dónde has sacado esta actividad?"
    )
    
    print("\n" + "="*20)
    if success:
        print("RESULTADO GLOBAL: APTO ✅")
        sys.exit(0)
    else:
        print("RESULTADO GLOBAL: NO APTO ❌")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
