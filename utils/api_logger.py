import time
import logging
from typing import Dict, Any, Optional

# Basic console logger
logger = logging.getLogger("APILogger")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

class APILogger:
    """
    A simple logger to log all external API calls (e.g., to PaddleOCR or LLMs for Extraction)
    as required by the system spec.
    """
    
    @staticmethod
    def log_call(service_name: str, endpoint: str, payload_summary: str, response_status: str, execution_time_ms: float, error_msg: Optional[str] = None):
        """
        Logs a single API call's metadata.
        In a real production system, this would write to a database or ELK stack.
        """
        log_data = {
            "service": service_name,
            "endpoint": endpoint,
            "payload": payload_summary,
            "status": response_status,
            "latency_ms": execution_time_ms
        }
        if error_msg:
            log_data["error"] = error_msg
            logger.error(f"EXTERNAL API CALL FAILED: {log_data}")
        else:
            logger.info(f"EXTERNAL API CALL SUCCESS: {log_data}")

def log_external_call(service_name: str, endpoint: str):
    """
    A decorator to automatically log synchronous external API calls.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                latency = (time.time() - start_time) * 1000
                
                # Try to summarize payload
                payload_summary = f"args: {len(args)}, kwargs: {list(kwargs.keys())}"
                
                APILogger.log_call(
                    service_name=service_name,
                    endpoint=endpoint,
                    payload_summary=payload_summary,
                    response_status="success",
                    execution_time_ms=latency
                )
                return result
            except Exception as e:
                latency = (time.time() - start_time) * 1000
                APILogger.log_call(
                    service_name=service_name,
                    endpoint=endpoint,
                    payload_summary="error during execution",
                    response_status="failed",
                    execution_time_ms=latency,
                    error_msg=str(e)
                )
                raise
        return wrapper
    return decorator
