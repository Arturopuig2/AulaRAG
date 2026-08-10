import os
import re
import fitz  # PyMuPDF
from PIL import Image
import io
from .database import SessionLocal
from . import models
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

# Database model for extracted book images
class MultimodalImage(models.Base):
    __tablename__ = "multimodal_images"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String, index=True, nullable=False)
    grade = Column(Integer, index=True, nullable=True)
    page_num = Column(Integer, nullable=False)
    image_url = Column(String, nullable=False)
    caption = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def extract_and_catalog_images(data_dir: str = "data/source_files", output_dir: str = "static/uploads/extracted_images"):
    """Scans PDFs in source_files, extracts diagrams/illustrations (>120x120), and registers them in DB."""
    os.makedirs(output_dir, exist_ok=True)
    db = SessionLocal()
    extracted_count = 0

    try:
        models.Base.metadata.create_all(bind=db.get_bind())
        
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                if file.endswith(".pdf"):
                    pdf_path = os.path.join(root, file)
                    rel_dir = os.path.basename(os.path.dirname(pdf_path))
                    subject = rel_dir.lower()
                    
                    # Extract grade from filename if available
                    grade = None
                    digits = [c for c in file if c.isdigit()]
                    if digits:
                        try:
                            grade = int("".join(digits[:2]))
                        except:
                            pass
                    
                    try:
                        doc = fitz.open(pdf_path)
                        for page_idx in range(len(doc)):
                            page = doc[page_idx]
                            image_list = doc.get_page_images(page_idx)
                            
                            # Get text snippet from page for captioning
                            page_text = page.get_text("text").strip()
                            caption_snippet = page_text[:200].replace("\n", " ") if page_text else f"Página {page_idx+1}"

                            for img_idx, img in enumerate(image_list):
                                xref = img[0]
                                base_image = doc.extract_image(xref)
                                image_bytes = base_image["image"]
                                image_ext = base_image["ext"]

                                # Filter out small icons/decorations using PIL
                                pil_img = Image.open(io.BytesIO(image_bytes))
                                width, height = pil_img.size
                                if width < 120 or height < 120:
                                    continue

                                img_filename = f"{subject}_g{grade or 0}_p{page_idx+1}_img{img_idx+1}.{image_ext}"
                                save_path = os.path.join(output_dir, img_filename)
                                image_url = f"/static/uploads/extracted_images/{img_filename}"

                                pil_img.save(save_path)
                                extracted_count += 1

                                # Check if already in DB
                                existing = db.query(MultimodalImage).filter(MultimodalImage.image_url == image_url).first()
                                if not existing:
                                    db_img = MultimodalImage(
                                        subject=subject,
                                        grade=grade,
                                        page_num=page_idx + 1,
                                        image_url=image_url,
                                        caption=caption_snippet
                                    )
                                    db.add(db_img)
                        doc.close()
                    except Exception as pe:
                        print(f"Error processing PDF {pdf_path}: {pe}")
        db.commit()
    except Exception as e:
        print(f"Error cataloging multimodal images: {e}")
    finally:
        db.close()
    
    print(f"[multimodal] Extraction completed. Total images cataloged: {extracted_count}")
    return extracted_count


def get_relevant_book_image(subject: str, grade: int = None, query_text: str = "") -> str:
    """Finds a relevant verified book image ONLY when there is a high-confidence match with the query.
       Returns None if no matching educational illustration exists to prevent showing incorrect images."""
    if not query_text or len(query_text.strip()) < 3:
        return None

    db = SessionLocal()
    try:
        q = db.query(MultimodalImage).filter(MultimodalImage.subject.ilike(f"%{subject}%"))
        if grade:
            q = q.filter((MultimodalImage.grade == grade) | (MultimodalImage.grade == None))

        all_imgs = q.all()
        if not all_imgs:
            return None

        # Filter out common stop words to focus on meaningful educational keywords
        stop_words = {"para", "como", "esta", "este", "esto", "sobre", "entre", "desde", "hasta", "hacer", "quiero", "repasar", "explicame", "dime", "teoria", "ejemplo", "ejemplos", "leccion"}
        query_words = [w.lower() for w in re.findall(r'\b[a-zA-ZáéíóúÁÉÍÓÚñÑ]{4,}\b', query_text) if w.lower() not in stop_words]

        if not query_words:
            return None

        # Search for images whose page text caption contains at least 2 key query terms or a strong unique topic match
        best_match = None
        max_matches = 0

        for img in all_imgs:
            if not img.caption:
                continue
            caption_lower = img.caption.lower()
            match_count = sum(1 for w in query_words if w in caption_lower)
            if match_count > max_matches:
                max_matches = match_count
                best_match = img.image_url

        # Require at least 2 matching key terms or 1 long specific term (>6 chars)
        if max_matches >= 2 or (max_matches == 1 and any(len(w) >= 7 for w in query_words if any(w in (img.caption or "").lower() for img in all_imgs))):
            return best_match

        # Strict: Return None if no high-confidence educational match found
        return None
    except Exception as e:
        print(f"Error getting book image: {e}")
        return None
    finally:
        db.close()


def audit_catalog_with_vision(limit: int = 100) -> dict:
    """Uses Gemini Vision AI to audit cataloged book images, deleting decorative graphics and enriching educational captions."""
    from .rag_engine import get_client, get_model_name
    client = get_client()
    model_name = get_model_name()
    db = SessionLocal()
    processed = 0
    kept = 0
    deleted = 0

    try:
        records = db.query(MultimodalImage).limit(limit).all()
        print(f"[Vision Audit] Auditing up to {len(records)} images with Gemini Vision...")

        for rec in records:
            file_path = rec.image_url.lstrip("/")
            if not os.path.exists(file_path):
                db.delete(rec)
                deleted += 1
                continue

            try:
                img = Image.open(file_path)
                prompt = (
                    "Analiza esta imagen extraída de un libro de texto de primaria.\n"
                    "Determina si es una LÁMINA DIDÁCTICA EDUCATIVA útil para explicar teoría (ej: diagramas, esquemas, figuras geométricas, tablas, mapas conceptuales) "
                    "o si es solo un dibujo decorativo/mascota/marco/encabezado sin valor didáctico autónomo.\n"
                    "Responde estrictamente en JSON: {\"is_educational\": true|false, \"description\": \"descripción didáctica breve\"}"
                )
                response = client.models.generate_content(
                    model=model_name,
                    contents=[img, prompt]
                )
                txt = response.text or ""
                # Parse JSON
                json_match = re.search(r'\{.*\}', txt, re.DOTALL)
                if json_match:
                    res = json.loads(json_match.group(0))
                    if not res.get("is_educational", False):
                        # Delete non-educational decorative graphic
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        db.delete(rec)
                        deleted += 1
                    else:
                        # Enrich caption with exact visual description
                        rec.caption = res.get("description", rec.caption)
                        kept += 1
                processed += 1
            except Exception as ve:
                print(f"Error analyzing image {rec.id}: {ve}")
                continue

        db.commit()
        print(f"[Vision Audit] Finished audit: {processed} processed, {kept} educational images kept, {deleted} decorative graphics purged.")
        return {"processed": processed, "kept": kept, "deleted": deleted}
    except Exception as e:
        print("Error during Vision catalog audit:", e)
        return {"error": str(e)}
    finally:
        db.close()
