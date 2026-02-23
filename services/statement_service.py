from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
from models.schemas import JobResultResponse
from utils.api_logger import log_external_call

class BaseExtractionService(ABC):
    """
    Abstract base class for all statement modules (Bank, Loan, Financials).
    Enforces separation of extraction, validation, and computation.
    """
    
    def process(self, file_path: str, request_data: Dict[str, Any]) -> JobResultResponse:
        """
        The main template method that orchestrates the flow.
        """
        # 1. Extract Data
        raw_extraction = self.extract(file_path, request_data)
        
        # 2. Validate extracted data against input
        validation_result = self.validate(raw_extraction, request_data)
        
        # 3. Compute domain-specific metrics and risks
        summary, risk_analysis = self.compute(raw_extraction, validation_result)
        
        # 4. Build and return the final response
        return self.build_response(validation_result, summary, risk_analysis)

    @abstractmethod
    def extract(self, file_path: str, request_data: Dict[str, Any]) -> Any:
        """
        Calls OCR / LLM to extract raw data.
        Concrete classes must implement this.
        """
        pass

    @abstractmethod
    def validate(self, extracted_data: Any, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates extracted data against user-provided request data.
        Concrete classes must implement this.
        """
        pass

    @abstractmethod
    def compute(self, extracted_data: Any, validation_result: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Computes financial summaries and risk metrics.
        Returns a tuple of (summary_dict, risk_dict).
        Concrete classes must implement this.
        """
        pass
        
    @abstractmethod
    def build_response(self, validation_result: Dict[str, Any], summary: Dict[str, Any], risk_analysis: Dict[str, Any]) -> JobResultResponse:
        """
        Constructs the final JobResultResponse object.
        """
        pass
