import os
import shutil
import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from services.ocr_service import OCRService
from services.face_service import FaceService
from services.matching_service import MatchingService
from services.pdf_utils import get_pdf_first_page_image

router = APIRouter()

# Initialize services
ocr_service = OCRService()
face_service = FaceService()
matching_service = MatchingService()

# Directory for temporary uploads
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/verify/aadhaar")
async def verify_aadhaar(
    file: UploadFile = File(...),
    photo: Optional[UploadFile] = File(None),
    name: Optional[str] = Form(None),
    dob: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
):
    """
    Verify an Aadhaar card.
    - file: Aadhaar card image or PDF (required)
    - photo: Selfie photo for face matching (optional)
    - name, dob, address: User-provided data to match against (optional)
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".pdf"]:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    file_id = str(uuid.uuid4())
    temp_path = os.path.join(UPLOAD_DIR, f"aadhaar_{file_id}{ext}")
    temp_photo_path = None

    try:
        # Save document file
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Prepare document image bytes for face detection
        if ext == ".pdf":
            try:
                doc_image_bytes = get_pdf_first_page_image(temp_path)
            except Exception as e:
                return JSONResponse(status_code=400, content={"status": "error", "message": f"Failed to extract image from PDF: {str(e)}"})
        else:
            with open(temp_path, "rb") as f:
                doc_image_bytes = f.read()

        # 1. OCR Extraction
        ocr_result = ocr_service.extract_data(temp_path)

        # Verify it detected as Aadhaar
        if ocr_result.get("document_type") != "Aadhaar Card":
            return JSONResponse(status_code=400, content={
                "status": "error",
                "message": "Document does not appear to be an Aadhaar card",
                "detected_type": ocr_result.get("document_type", "Unknown")
            })

        # 2. Face Detection on document
        face_score, num_faces = face_service.detect_face(doc_image_bytes)

        # 3. Build extracted data
        extracted_data = {
            "name": ocr_result.get("name"),
            "dob": ocr_result.get("dob"),
            "id_number": ocr_result.get("id_number"),
            "gender": ocr_result.get("gender"),
            "father_name": ocr_result.get("father_name"),
            "address": ocr_result.get("address"),
        }

        # 4. Match scores (only for provided fields)
        verification_scores = {}

        if name:
            verification_scores["name_match"] = matching_service.match_name(
                extracted_data.get("name"), name
            )

        if dob:
            verification_scores["dob_match"] = matching_service.match_dob(
                extracted_data.get("dob"), dob
            )

        if address:
            verification_scores["address_match"] = matching_service.match_address(
                extracted_data.get("address"), address
            )

        # 5. Photo matching
        if photo:
            temp_photo_path = os.path.join(UPLOAD_DIR, f"photo_{file_id}.jpg")
            with open(temp_photo_path, "wb") as buffer:
                shutil.copyfileobj(photo.file, buffer)
            with open(temp_photo_path, "rb") as f:
                selfie_bytes = f.read()

            verification_scores["photo_match"] = face_service.compare_faces(
                doc_image_bytes, selfie_bytes
            )

        # 6. Overall score
        overall_score = matching_service.calculate_overall_score(verification_scores)
        verification_scores["overall_score"] = overall_score

        # 7. Build response
        response = {
            "status": "success",
            "document_type": "Aadhaar Card",
            "extracted_data": extracted_data,
            "face_detection": {
                "face_found_on_document": face_score > 0,
                "faces_detected": num_faces,
            },
            "verification_scores": verification_scores if verification_scores else None,
            "is_verified": overall_score >= 0.6 if verification_scores else None,
        }

        return JSONResponse(content=response)

    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if temp_photo_path and os.path.exists(temp_photo_path):
            os.remove(temp_photo_path)
