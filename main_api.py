from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import shutil
import os
import uuid
import json
from typing import List, Optional
from services.ocr_service import OCRService
from services.face_service import FaceService
from services.table_service import TableExtractionService
from services.pdf_utils import get_pdf_first_page_image

app = FastAPI(title="Aadhaar and PAN Card Verification & Table Extraction API")

# Initialize services
ocr_service = OCRService()
face_service = FaceService()
table_service = TableExtractionService()

# Directory for temporary uploads
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/verify")
async def verify_document(file: UploadFile = File(...)):
    """
    Upload an Aadhaar or PAN card image or PDF to extract data and verify.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".pdf"]:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    # Unique filename to avoid collisions
    file_id = str(uuid.uuid4())
    temp_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")

    try:
        # Save uploaded file
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 1. Prepare image for face detection
        if ext == ".pdf":
            try:
                image_bytes = get_pdf_first_page_image(temp_path)
            except Exception as e:
                return JSONResponse(status_code=400, content={"status": "error", "message": f"Failed to extract image from PDF: {str(e)}"})
        else:
            with open(temp_path, "rb") as f:
                image_bytes = f.read()

        # 2. Face Detection
        face_score, num_faces = face_service.detect_face(image_bytes)

        # 3. OCR and Data Extraction
        ocr_result = ocr_service.extract_data(temp_path)

        # Build response
        response_data = {
            "status": "success",
            "document_info": ocr_result,
            "face_verification": {
                "human_face_score": face_score,
                "faces_detected": num_faces
            },
            "overall_verification": {
                "is_valid_document": ocr_result.get("document_score", 0) > 0.6 and face_score > 0.5,
                "confidence_score": (ocr_result.get("document_score", 0) + face_score) / 2
            }
        }

        return JSONResponse(content=response_data)

    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
