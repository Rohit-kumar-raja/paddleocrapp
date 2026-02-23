import os
# ---- Must be set BEFORE any PaddlePaddle / PaddleOCR imports ----
os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["DISABLE_MODEL_SOURCE_CHECK"] = "True"

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import shutil
import uuid
import json
from typing import List, Optional
from services.ocr_service import OCRService
from services.face_service import FaceService
from services.table_service import TableExtractionService
from services.matching_service import MatchingService
from services.pdf_utils import get_pdf_first_page_image

app = FastAPI(title="Aadhaar and PAN Card Verification & Table Extraction API")

# Initialize services
ocr_service = OCRService()
face_service = FaceService()
table_service = TableExtractionService()
matching_service = MatchingService()

# Directory for temporary uploads
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)



@app.post("/extract-table")
async def extract_table(
    file: UploadFile = File(...),
    columns: Optional[str] = None
):
    """
    Extracts tabular data from a PDF or image.
    Optional 'columns' parameter as a JSON list string, e.g., '["Date", "Credit"]'.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".pdf"]:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    file_id = str(uuid.uuid4())
    temp_path = os.path.join(UPLOAD_DIR, f"table_{file_id}{ext}")

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        target_cols = None
        if columns:
            try:
                target_cols = json.loads(columns)
                if not isinstance(target_cols, list):
                    raise ValueError("Columns must be a list")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid columns format: {str(e)}")

        table_data = table_service.extract_table_data(temp_path, target_cols)

        return JSONResponse(content={
            "status": "success",
            "filename": file.filename,
            "table_data": table_data
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)




app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/app")
async def serve_app():
    from fastapi.responses import FileResponse
    return FileResponse("static/index.html")

# ===================== ROUTERS =====================
from routers import aadhaar_router, pan_router, extractor_api
app.include_router(aadhaar_router.router)
app.include_router(pan_router.router)
app.include_router(extractor_api.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

