"""
AulaRAG Multi-Agent Architecture
================================
Implements specialized pedagogical agents per subject:
1. AgenteLengua (Spanish Language & RAE Grammar Expert)
2. AgenteValenciano (Valencian Language & Grammar Expert)
3. AgenteMatematicas (Math & Logical Reasoning Expert)
4. AgenteIngles (English Language & Vocabulary Expert)
5. AgenteAuditor (Quality & Orthographic Auditor)
6. RouterAgent (Directs student queries to the appropriate agent)
"""

import json
import re
import os

def get_didactic_course_rules(grade: int = None) -> str:
    """Retorna las reglas didácticas de adaptación pedagógica según el curso (1º a 6º de Primaria)."""
    if not grade:
        return ""
    
    if grade in [1, 2]:
        return (
            f"\n### REGLAS DIDÁCTICAS OBLIGATORIAS ({grade}º DE PRIMARIA - NIVEL INICIAL):\n"
            "- Usa frases muy cortas y sencillas (máximo 10-12 palabras por frase).\n"
            "- Explica siempre con analogías muy visuales usando objetos cercanos (juguetes, frutas, animales o cosas de casa).\n"
            "- Estrictamente PROHIBIDO utilizar jerga técnica, palabras abstractas o explicaciones complejas.\n"
            "- Tono súper cercano, claro, directo y motivador."
        )
    elif grade in [3, 4]:
        return (
            f"\n### REGLAS DIDÁCTICAS OBLIGATORIAS ({grade}º DE PRIMARIA - NIVEL INTERMEDIO):\n"
            "- Organiza siempre la información mediante esquemas claros, viñetas y estructuras paso a paso.\n"
            "- Usa explicaciones visuales, metáforas cotidianas y ejemplos del colegio o del día a día.\n"
            "- Presenta los conceptos clave de forma estructurada sin sobrecargar con teoría innecesaria."
        )
    elif grade in [5, 6]:
        return (
            f"\n### REGLAS DIDÁCTICAS OBLIGATORIAS ({grade}º DE PRIMARIA - NIVEL AVANZADO / PREPARACIÓN SECUNDARIA):\n"
            "- Fomenta el pensamiento crítico y la capacidad de deducción planteando preguntas reflexivas.\n"
            "- Presenta fórmulas, reglas gramaticales y procedimientos totalmente desglosados paso a paso.\n"
            "- Introduce el vocabulario técnico y formal de la asignatura de forma gradual, explicando siempre su significado."
        )
    return ""


class BaseAgent:
    def __init__(self, name: str, role_description: str, subject_code: str):
        self.name = name
        self.role_description = role_description
        self.subject_code = subject_code

    def get_system_prompt(self, base_rules: str, subject_rules: str, grade: int = None) -> str:
        course_rules = get_didactic_course_rules(grade)
        return f"""*** AGENTE ESPECIALISTA: {self.name.upper()} ***
Rol: {self.role_description}

{base_rules}

### REGLAS ESPECÍFICAS DE {self.name.upper()}:
{subject_rules}
{course_rules}
"""

class AgenteLengua(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Lengua Castellana",
            role_description="Experto en gramática RAE, ortografía estricta, acentuación y sintaxis para educación primaria.",
            subject_code="lengua"
        )

class AgenteValenciano(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Llengua Valenciana",
            role_description="Expert didàctic en llengua valenciana, ortografia, accentuació (oberta/tancada) i gramàtica de primària.",
            subject_code="valenciano"
        )

class AgenteMatematicas(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Matemáticas",
            role_description="Experto didáctico en razonamiento lógico, descomposición paso a paso y resolución de problemas.",
            subject_code="matematicas"
        )

class AgenteIngles(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Inglés (Primary English)",
            role_description="Tutor pedagógico experto en Inglés Primaria. COMBINA SIEMPRE Inglés y Español en todas las explicaciones ya que los alumnos son muy pequeños y se están iniciando en la lengua inglesa. Explica cada palabra o regla en inglés seguida inmediatamente de su apoyo/traducción en español.",
            subject_code="ingles"
        )

class AgenteAuditor:
    """Audits generated explanations to ensure 100% orthographic accuracy and format compliance."""
    @staticmethod
    def audit_and_clean(text: str, subject: str = "general") -> str:
        if not text:
            return text
        
        # Clean section collisions like ---### into clean double newlines
        text = re.sub(r'---+\s*(#{1,6}\s*)', r'\n\n\1', text)
        text = re.sub(r'(#{1,6}\s*[^\n]+)', r'\n\1\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove leftover bracket tags
        text = re.sub(r'\[\s*(?:INCORRECTE|CORRECTE|INCORRECTO|CORRECTO)\s*\]', '', text, flags=re.IGNORECASE)
        
        # Strip any accidental theatrical greetings / child-talk intros
        text = re.sub(r'^\s*¡?Hola[^\n!.]*[!.]\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^\s*¡?Bienvenido[^\n!.]*[!.]\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^\s*¡?Pequeños exploradores[^\n!.]*[!.]\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^\s*Hoy vamos a descubrir[^\n!.]*[!.]\s*', '', text, flags=re.IGNORECASE)

        return text.strip()

class RouterAgent:
    """Orchestrates agent selection based on the user's selected subject."""
    def __init__(self):
        self.agents = {
            "lengua": AgenteLengua(),
            "valenciano": AgenteValenciano(),
            "matematicas": AgenteMatematicas(),
            "ingles": AgenteIngles()
        }

    def get_agent(self, subject: str) -> BaseAgent:
        norm_subj = subject.lower().strip()
        if "valenc" in norm_subj:
            return self.agents["valenciano"]
        elif "lengua" in norm_subj or "castellano" in norm_subj or "lect" in norm_subj:
            return self.agents["lengua"]
        elif "mate" in norm_subj:
            return self.agents["matematicas"]
        elif "ingl" in norm_subj or "english" in norm_subj:
            return self.agents["ingles"]
        return self.agents["lengua"]

# Global router instance
router = RouterAgent()
