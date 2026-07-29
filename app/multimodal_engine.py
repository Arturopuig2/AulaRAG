import os
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
    """Finds a relevant extracted book image for the given subject/grade/topic query."""
    db = SessionLocal()
    try:
        q = db.query(MultimodalImage).filter(MultimodalImage.subject.ilike(f"%{subject}%"))
        if grade:
            q = q.filter((MultimodalImage.grade == grade) | (MultimodalImage.grade == None))

        all_imgs = q.all()
        if not all_imgs:
            return None

        if query_text:
            query_words = [w.lower() for w in query_text.split() if len(w) > 3]
            for img in all_imgs:
                if img.caption and any(w in img.caption.lower() for w in query_words):
                    return img.image_url

        # Return first cataloged image for that subject/grade if no exact text match
        return all_imgs[0].image_url
    except Exception as e:
        print(f"Error getting book image: {e}")
        return None
    finally:
        db.close()
