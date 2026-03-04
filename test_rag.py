import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.rag_engine import existing_files_cache, get_pdf_part_for_context

print("Files in cache:", existing_files_cache.keys())
print("Testing valenciano 1º:")
part = get_pdf_part_for_context("valenciano", "1º de primaria")
print("Result for valenciano 1:", part)
if part:
    print("URI:", part.file_data.file_uri)

print("\nTesting lengue 1º:")
part = get_pdf_part_for_context("lengua", "1º de primaria")
print("Result for lengua 1:", part)
if part:
    print("URI:", part.file_data.file_uri)
