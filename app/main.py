from fastapi import FastAPI, Request, Form, UploadFile, File, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import shutil
import json
from .rag_engine import get_gemini_response, upload_new_file_to_gemini

app = FastAPI(title="Aula RAG AI Assistant")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/temario/lengua")
async def get_temario_lengua():
    file_path = os.path.join(os.path.dirname(__file__), "..", "data", "source_files", "lengua", "temario_lengua")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.post("/chat")
async def chat_endpoint(message: str = Form(...), subject: str = Form("general"), course_level: str = Form("")):
    # This endpoint receives a message from the user and returns the AI response
    try:
        response_text = await get_gemini_response(message, subject, course_level)
        return {"response": response_text}
    except Exception as e:
        return {"error": str(e)}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), subject: str = Form("general")):
    # Validate PDF
    if not file.filename.endswith(".pdf"):
        return {"error": "Only PDF files are supported"}
        
    try:
        # Save locally in the specific subject folder
        source_dir = os.path.join(os.path.dirname(__file__), "..", "data", "source_files", subject)
        os.makedirs(source_dir, exist_ok=True)
        file_path = os.path.join(source_dir, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Upload to Gemini and refresh session in the background so we don't block the UI
        # (For this simplified version await it directly to ensure it's ready)
        # We also pass the subject so the engine knows what changed
        success = upload_new_file_to_gemini(file_path, subject)
        
        if success:
            return {"filename": file.filename, "status": "Successfully uploaded and indexed by Gemini"}
        else:
            return {"error": "Failed to index file in Gemini API"}
            
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
