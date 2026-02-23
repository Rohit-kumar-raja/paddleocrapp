from enum import Enum

class ExtractType(str, Enum):
    """
    Enum for selecting the type of extraction/API.
    """
    BANK_STATEMENT = "bank_statement"
    LOAN_DOCUMENT = "loan_document"
    FINANCIAL_DOCUMENT = "financial_document"
    TABLE = "table"

class FinancialDocumentType(str, Enum):
    """
    Enum for the specific type of company financial document.
    """
    BALANCE_SHEET = "balance_sheet"
    STOCK_STATEMENT = "stock_statement"

class APIStatus(str, Enum):
    """
    Enum for the status of the API request.
    """
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"

class JobStatus(str, Enum):
    """
    Enum for the status of the async OCR job in the queue.
    """
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
