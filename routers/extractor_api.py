from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import os
import shutil
import uuid
from typing import Optional

from models.enums import ExtractType, FinancialDocumentType, JobStatus, APIStatus
from models.schemas import JobResponse
from services.queue_service import queue_service, process_job_async
from services.bank_statement_service import BankStatementService
from services.loan_service import LoanStatementService
from services.financial_service import FinancialStatementService

router = APIRouter()

# Instantiate services
bank_service = BankStatementService()
loan_service = LoanStatementService()
financial_service = FinancialStatementService()

UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/extract", response_model=JobResponse)
async def extract_document(
    background_tasks: BackgroundTasks,
    extract_type: ExtractType = Form(...),
    file: UploadFile = File(...),
    account_name: str = Form(...),
    account_number: str = Form(...),
    institute_name: Optional[str] = Form(None),
    bank_name: Optional[str] = Form(None),
    tenure_months: Optional[int] = Form(None),
    tenure: Optional[str] = Form(None),
    doc_type: Optional[FinancialDocumentType] = Form(None)
):
    """
    Unified endpoint for processing complex financial documents asynchronously.
    Creates a job and returns the Job ID for polling.
    """
    # 1. Validate incoming data based on type
    if extract_type == ExtractType.BANK_STATEMENT and (not bank_name or not tenure_months):
        raise HTTPException(status_code=400, detail="bank_name and tenure_months are required for bank statements")
    
    if extract_type == ExtractType.LOAN_DOCUMENT and (not institute_name or not tenure_months):
        raise HTTPException(status_code=400, detail="institute_name and tenure_months are required for loan documents")
        
    if extract_type == ExtractType.FINANCIAL_DOCUMENT and (not institute_name or not tenure or not doc_type):
         raise HTTPException(status_code=400, detail="institute_name, tenure, and doc_type are required for financial documents")

    # 2. Save the uploaded file temporarily
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".jpg", ".jpeg", ".png"]:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
        
    file_id = str(uuid.uuid4())
    temp_path = os.path.join(UPLOAD_DIR, f"{extract_type.value}_{file_id}{ext}")
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # 3. Create a Job ID in our Queue system
    job_id = queue_service.create_job()
    
    # Pack the request data nicely for the underlying service
    request_data = {
        "account_name": account_name,
        "account_number": account_number,
        "institute_name": institute_name,
        "bank_name": bank_name,
        "tenure_months": tenure_months,
        "tenure": tenure,
        "doc_type": doc_type
    }
    
    # 4. Route to the right service
    processor = None
    if extract_type == ExtractType.BANK_STATEMENT:
        processor = bank_service.process
    elif extract_type == ExtractType.LOAN_DOCUMENT:
        processor = loan_service.process
    elif extract_type == ExtractType.FINANCIAL_DOCUMENT:
        # Note: FinancialStatementService needs doc_type in its extract method
        processor = financial_service.process
    else:
        # Failsafe
        queue_service.mark_job_failed(job_id, f"Unsupported extract_type: {extract_type}")
        return JSONResponse(status_code=400, content={"message": f"Unsupported extract_type: {extract_type}"})

    # 5. Hand off to background tasks
    if processor:
         background_tasks.add_task(process_job_async, job_id, processor, temp_path, request_data)

    return JobResponse(
        api_status=APIStatus.SUCCESS,
        job_id=job_id,
        job_status=JobStatus.CREATED,
        message="Job created successfully. Poll /extract/status/{job_id} for results."
    )

@router.get("/extract/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Poll this endpoint to get the status and result of the extraction job.
    """
    job = queue_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    # Standardised Failure matching spec requirement
    if job.job_status == JobStatus.FAILED:
         return JSONResponse(status_code=500, content={
            "api_status": "failed",
            "job_status": "failed",
            "failed_message": job.failed_message or "Something went wrong. Try again."
        })
        
    return job
