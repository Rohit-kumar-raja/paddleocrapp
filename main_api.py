import os
# ---- Must be set BEFORE any PaddlePaddle / PaddleOCR imports ----
os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["DISABLE_MODEL_SOURCE_CHECK"] = "True"

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
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


# ===================== AADHAAR CARD VERIFICATION =====================
@app.post("/verify/aadhaar")
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


# ===================== PAN CARD VERIFICATION =====================
@app.post("/verify/pan")
async def verify_pan(
    file: UploadFile = File(...),
    photo: Optional[UploadFile] = File(None),
    name: Optional[str] = Form(None),
    dob: Optional[str] = Form(None),
):
    """
    Verify a PAN card.
    - file: PAN card image or PDF (required)
    - photo: Selfie photo for face matching (optional)
    - name, dob: User-provided data to match against (optional)
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".pdf"]:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    file_id = str(uuid.uuid4())
    temp_path = os.path.join(UPLOAD_DIR, f"pan_{file_id}{ext}")
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

        # Verify it detected as PAN
        if ocr_result.get("document_type") != "PAN Card":
            return JSONResponse(status_code=400, content={
                "status": "error",
                "message": "Document does not appear to be a PAN card",
                "detected_type": ocr_result.get("document_type", "Unknown")
            })

        # 2. Face Detection on document
        face_score, num_faces = face_service.detect_face(doc_image_bytes)

        # 3. Build extracted data
        extracted_data = {
            "name": ocr_result.get("name"),
            "dob": ocr_result.get("dob"),
            "id_number": ocr_result.get("id_number"),
            "father_name": ocr_result.get("father_name"),
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
            "document_type": "PAN Card",
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
