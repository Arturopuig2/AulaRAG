import os
import PyPDF2

pdf_dir = "/Users/arturo/Desktop/Aula_RAG/AulaRAG/data/source_files/lengua/"

for filename in os.listdir(pdf_dir):
    if filename.endswith(".pdf"):
        path = os.path.join(pdf_dir, filename)
        try:
            with open(path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text and "ventana" in text.lower():
                        print(f"Found 'ventana' in {filename} p.{i+1}")
        except Exception as e:
            pass
