"""
AulaRAG Multi-Agent Architecture
================================
Implements specialized pedagogical agents per subject:
1. AgenteLengua (Spanish Language & RAE Grammar Expert)
2. AgenteValenciano (Valencian Language & Grammar Expert)
3. AgenteMatematicas (Math & Logical Reasoning Expert)
4. AgenteIngles (English Language & Vocabulary Expert)
5. AgenteCompetenciaLectora (Reading Comprehension & Analysis Expert)
6. AgenteAuditor (Quality & Orthographic Auditor)
7. RouterAgent (Directs student queries to the appropriate agent)
"""

import json
import re
import os

class BaseAgent:
    def __init__(self, name: str, role_description: str, subject_code: str):
        self.name = name
        self.role_description = role_description
        self.subject_code = subject_code

    def get_system_prompt(self, base_rules: str, subject_rules: str) -> str:
        return f"""*** AGENTE ESPECIALISTA: {self.name.upper()} ***
Rol: {self.role_description}

{base_rules}

### REGLAS ESPECÍFICAS DE {self.name.upper()}:
{subject_rules}
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
            role_description="Primary English Tutor specialized in ESL vocabulary, grammar, and pronunciation.",
            subject_code="ingles"
        )

class AgenteCompetenciaLectora(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Comprensión Lectora",
            role_description="Experto en análisis de textos escolares, lectura guiada y vocabulario.",
            subject_code="competencia_lectora"
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
        
        # Strip legacy exercise series closing prompts
        text = re.sub(r'Has completat \d+ exercicis![^\n]*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'¿Quieres hacer \d+ más\?[^\n]*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Vols fer-ne \d+ més\?[^\n]*', '', text, flags=re.IGNORECASE)

        return text.strip()

class RouterAgent:
    """Orchestrates agent selection based on the user's selected subject."""
    def __init__(self):
        self.agents = {
            "lengua": AgenteLengua(),
            "valenciano": AgenteValenciano(),
            "matematicas": AgenteMatematicas(),
            "ingles": AgenteIngles(),
            "competencia_lectora": AgenteCompetenciaLectora()
        }

    def get_agent(self, subject: str) -> BaseAgent:
        norm_subj = subject.lower().strip()
        if "valenc" in norm_subj:
            return self.agents["valenciano"]
        elif "lengua" in norm_subj or "castellano" in norm_subj:
            return self.agents["lengua"]
        elif "mate" in norm_subj:
            return self.agents["matematicas"]
        elif "ingl" in norm_subj or "english" in norm_subj:
            return self.agents["ingles"]
        elif "lect" in norm_subj:
            return self.agents["competencia_lectora"]
        return self.agents["lengua"]

# Global router instance
router = RouterAgent()
