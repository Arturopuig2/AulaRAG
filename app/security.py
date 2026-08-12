"""
Security, Sanitization, Prompt Injection Defense, and Child Safety Guardrails for AulaRAG.
"""

import html
import re
from typing import Tuple

# --- Dangerous HTML / Script Patterns (XSS) ---
XSS_PATTERNS = [
    r'<\s*script[^>]*>.*?<\s*/\s*script\s*>',
    r'<\s*iframe[^>]*>.*?<\s*/\s*iframe\s*>',
    r'<\s*object[^>]*>.*?<\s*/\s*object\s*>',
    r'<\s*embed[^>]*>.*?<\s*/\s*embed\s*>',
    r'on\w+\s*=\s*["\'][^"\']*["\']',
    r'javascript\s*:',
    r'vbscript\s*:',
    r'data\s*:\s*text/html',
]

# --- Prompt Injection Patterns ---
PROMPT_INJECTION_PATTERNS = [
    r'ignore\s+(all\s+)?(previous|prior)\s+instructions',
    r'forget\s+(all\s+)?(previous|prior)\s+rules',
    r'system\s+prompt',
    r'revela\s+tus\s+instrucciones',
    r'ignora\s+las\s+instrucciones\s+anteriores',
    r'olvida\s+tus\s+reglas',
    r'you\s+are\s+now\s+in\s+dan\s+mode',
    r'jailbreak',
]

# --- PII (Personally Identifiable Information) Patterns ---
PHONE_PATTERN = r'\b(?:\+34\s*)?[6789]\d{2}(?:[\s.-]?\d{3}){2}\b'
EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'


def sanitize_input_text(text: str) -> str:
    """
    Sanitizes raw user input text to prevent XSS, HTML injections, and prompt manipulation.
    """
    if not text:
        return ""
    
    clean_text = text
    
    # 1. Remove dangerous script and iframe tags
    for pattern in XSS_PATTERNS:
        clean_text = re.sub(pattern, '', clean_text, flags=re.IGNORECASE | re.DOTALL)
        
    # 2. Neutralize HTML entities for brackets
    clean_text = clean_text.replace('<', '&lt;').replace('>', '&gt;')
    
    # 3. Strip prompt injection triggers
    for pattern in PROMPT_INJECTION_PATTERNS:
        clean_text = re.sub(pattern, '[FILTRADO POR SEGURIDAD]', clean_text, flags=re.IGNORECASE)
        
    return clean_text.strip()


def sanitize_markdown_output(markdown_text: str) -> str:
    """
    Sanitizes AI-generated Markdown/HTML before sending it to the client to ensure no raw XSS payload exists.
    """
    if not markdown_text:
        return ""
        
    clean_md = markdown_text
    # Strip dangerous executable tags while preserving safe markdown formatting
    for pattern in XSS_PATTERNS:
        clean_md = re.sub(pattern, '', clean_md, flags=re.IGNORECASE | re.DOTALL)
        
    return clean_md


def audit_child_safety_and_pii(text: str) -> Tuple[bool, str]:
    """
    Audits input/output text for child safety and PII leaks.
    Returns (is_safe: bool, sanitized_or_reason_text: str).
    """
    if not text:
        return True, ""
        
    redacted_text = text
    
    # Redact email addresses
    if re.search(EMAIL_PATTERN, redacted_text):
        redacted_text = re.sub(EMAIL_PATTERN, '[CORREO RESERVADO POR PRIVACIDAD]', redacted_text)
        
    # Redact phone numbers
    if re.search(PHONE_PATTERN, redacted_text):
        redacted_text = re.sub(PHONE_PATTERN, '[TELÉFONO RESERVADO POR PRIVACIDAD]', redacted_text)
        
    # Check for prompt injection jailbreaks
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return False, "La consulta contiene patrones no permitidos por la política de seguridad escolar."
            
    return True, redacted_text
