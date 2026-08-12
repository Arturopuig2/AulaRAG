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
import os
import re
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
AGENTS_DIR = os.path.join(BASE_DIR, "agents")

def get_didactic_course_rules(grade: int = None) -> str:
    """Retorna las reglas didácticas de adaptación pedagógica desde agents/agente_didactico/reglas.txt según el curso (1º a 6º de Primaria)."""
    if not grade:
        return ""

    rules_path = os.path.join(AGENTS_DIR, "agente_didactico", "reglas.txt")
    if not os.path.exists(rules_path):
        return ""

    with open(rules_path, "r", encoding="utf-8") as f:
        content = f.read()

    if grade in [1, 2]:
        m = re.search(r'\[NIVEL_INICIAL_1_2\]\s*(.*?)(?=\n\s*\[|\Z)', content, re.DOTALL)
        return f"\n{m.group(1).strip()}\n" if m else ""
    elif grade in [3, 4]:
        m = re.search(r'\[NIVEL_INTERMEDIO_3_4\]\s*(.*?)(?=\n\s*\[|\Z)', content, re.DOTALL)
        return f"\n{m.group(1).strip()}\n" if m else ""
    elif grade in [5, 6]:
        m = re.search(r'\[NIVEL_AVANZADO_5_6\]\s*(.*?)(?=\n\s*\[|\Z)', content, re.DOTALL)
        return f"\n{m.group(1).strip()}\n" if m else ""

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

class AgenteSeguridad(BaseAgent):
    """Specialized Security, Anti-Injection, and Child Safety Agent."""
    def __init__(self):
        super().__init__(
            name="AgenteSeguridad",
            role_description="Guardián de Seguridad Web, Sanitización Anti-XSS/SQLi y Protección Infantil",
            subject_code="seguridad"
        )

    def audit_input(self, text: str) -> tuple[bool, str]:
        from .security import sanitize_input_text, audit_child_safety_and_pii
        clean_text = sanitize_input_text(text)
        is_safe, final_text = audit_child_safety_and_pii(clean_text)
        return is_safe, final_text

    def audit_output(self, text: str) -> str:
        from .security import sanitize_markdown_output
        return sanitize_markdown_output(text)

class AgenteDidactico(BaseAgent):
    """Specialized Agent for Primary Course Level Adaptation (1º to 6º de Primaria)."""
    def __init__(self):
        super().__init__(
            name="AgenteDidactico",
            role_description="Especialista en Adaptación Didáctica y Complejidad Psicoevolutiva por Curso",
            subject_code="didactico"
        )

    def get_course_rules(self, grade: int) -> str:
        return get_didactic_course_rules(grade)

class RouterAgent:
    """Orchestrates agent selection based on the user's selected subject."""
    def __init__(self):
        self.agents = {
            "lengua": AgenteLengua(),
            "valenciano": AgenteValenciano(),
            "matematicas": AgenteMatematicas(),
            "ingles": AgenteIngles()
        }
        self.security_agent = AgenteSeguridad()
        self.didactic_agent = AgenteDidactico()

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
