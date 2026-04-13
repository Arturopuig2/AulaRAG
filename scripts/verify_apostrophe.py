import re
import sys

def clean_ai_text(text: str) -> str:
    if not text:
        return text
    
    # Simulate spacing rules from original file
    text = re.sub(r'([.!?,;:])([a-zA-ZáéíóúÁÉÍÓÚñÑ])', r'\1 \2', text)
    
    # THE FIX
    text = re.sub(r'"([^"]+)"', r'**\1**', text)
    text = re.sub(r"(?<![a-zA-ZáéíóúÁÉÍÓÚñÑ])'([^']+)'(?![a-zA-ZáéíóúÁÉÍÓÚñÑ])", r"**\1**", text)

    return text

test_cases = [
    ("En valencià, s'escriu d'una manera.", "En valencià, s'escriu d'una manera."),
    ("La lletra 'P' i la 'B' sonen semblant.", "La lletra **P** i la **B** sonen semblant."),
    ("L'última lletra és una c.", "L'última lletra és una c."),
    ("M'agrada molt.", "M'agrada molt."),
    ("Contingut en 'negreta'.", "Contingut en **negreta**."),
    ("Contingut en \"negreta\".", "Contingut en **negreta**.")
]

success = True
for tc, expected in test_cases:
    output = clean_ai_text(tc)
    if output == expected:
        print(f"✅ PASS: {tc} -> {output}")
    else:
        print(f"❌ FAIL: {tc}")
        print(f"   Expected: {expected}")
        print(f"   Got:      {output}")
        success = False

if not success:
    sys.exit(1)
