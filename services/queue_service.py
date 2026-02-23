import uuid
from typing import Dict, Any, Optional
from models.enums import JobStatus, APIStatus
from models.schemas import JobResultResponse
import traceback
import asyncio

class QueueService:
    """
    A simple in-memory queue service to handle async OCR jobs.
    In production, this would be backed by Redis/Celery and a persistent DB.
    """
    def __init__(self):
        # In-memory storage for job statuses and results
        self.jobs: Dict[str, JobResultResponse] = {}

    def create_job(self) -> str:
        """
        Creates a new job and returns the job ID.
        """
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = JobResultResponse(
            api_status=APIStatus.PENDING,
            job_status=JobStatus.CREATED
        )
        return job_id

    def get_job(self, job_id: str) -> Optional[JobResultResponse]:
        """
        Retrieves the current status/result of a job.
        """
        return self.jobs.get(job_id)

    def update_job(self, job_id: str, result: JobResultResponse):
        """
        Updates the job with the final result.
        """
        self.jobs[job_id] = result

    def mark_job_failed(self, job_id: str, error_message: str):
        """
        Marks a job as failed and stores the error message.
        """
        self.jobs[job_id] = JobResultResponse(
            api_status=APIStatus.FAILED,
            job_status=JobStatus.FAILED,
            failed_message=error_message
        )

# Global singleton instance for the queue service
queue_service = QueueService()

async def process_job_async(job_id: str, processor_func, *args, **kwargs):
    """
    The background task that actually runs the extraction logic.
    """
    try:
        # Update status to IN_PROGRESS
        job = queue_service.get_job(job_id)
        if job:
            job.job_status = JobStatus.IN_PROGRESS
            queue_service.update_job(job_id, job)
        
        # In a real async system, processor_func might be a blocking call
        # that we'd run in an executor, but we assume it might be async here.
        if asyncio.iscoroutinefunction(processor_func):
            result = await processor_func(*args, **kwargs)
        else:
             # Run synchronous processors in a threadpool to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, processor_func, *args)
            
        # The processor_func should return a JobResultResponse
        if isinstance(result, JobResultResponse):
            result.api_status = APIStatus.SUCCESS
            result.job_status = JobStatus.COMPLETED
            queue_service.update_job(job_id, result)
        else:
             queue_service.mark_job_failed(job_id, "Processor returned an invalid format")

    except Exception as e:
        error_msg = f"Something went wrong. Try again. Detail: {str(e)}"
        print(f"Job {job_id} failed: {traceback.format_exc()}")
        queue_service.mark_job_failed(job_id, error_msg)
