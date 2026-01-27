from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import shutil
import os
import uuid
from services.ocr_service import OCRService
from services.face_service import FaceService

app = FastAPI(title="Aadhaar and PAN Card Verification API")

# Initialize services
ocr_service = OCRService()
face_service = FaceService()

# Directory for temporary uploads
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/verify")
async def verify_document(file: UploadFile = File(...)):
    """
    Upload an Aadhaar or PAN card image to extract data and verify.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    # Unique filename to avoid collisions
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    temp_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")

    try:
        # Save uploaded file
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Read file for face detection (using bytes)
        with open(temp_path, "rb") as f:
            image_bytes = f.read()

        # 1. Face Detection
        face_score, num_faces = face_service.detect_face(image_bytes)

        # 2. OCR and Data Extraction
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
                "is_valid_document": ocr_result["document_score"] > 0.6 and face_score > 0.5,
                "confidence_score": (ocr_result["document_score"] + face_score) / 2
            }
        }

        return JSONResponse(content=response_data)

    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
