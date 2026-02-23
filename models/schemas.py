from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from models.enums import APIStatus, JobStatus, ExtractType, FinancialDocumentType

# ==========================================
# Generic Job Models
# ==========================================

class JobResponse(BaseModel):
    api_status: APIStatus = APIStatus.SUCCESS
    job_id: str
    job_status: JobStatus
    message: Optional[str] = None

class JobResultResponse(BaseModel):
    api_status: APIStatus
    job_status: JobStatus
    failed_message: Optional[str] = None
    # Depending on the module, these will be populated
    validation_result: Optional[Dict[str, Any]] = None
    statement_summary: Optional[Dict[str, Any]] = None
    risk_analysis: Optional[Dict[str, Any]] = None
    # For Loan
    loan_summary: Optional[Dict[str, Any]] = None
    risk_indicators: Optional[Dict[str, Any]] = None
    # For Financials
    financial_metrics: Optional[Dict[str, Any]] = None

# ==========================================
# Request Models (Used by the routers for type hinting, though data might come via Form)
# ==========================================

class BaseStatementRequest(BaseModel):
    account_name: str
    account_number: str

class BankStatementRequest(BaseStatementRequest):
    tenure_months: int
    bank_name: str

class LoanStatementRequest(BaseStatementRequest):
    tenure_months: int
    institute_name: str

class FinancialDocumentRequest(BaseStatementRequest):
    tenure: str # FY or period
    institute_name: str
    doc_type: FinancialDocumentType

# ==========================================
# Extraction Models (Internal structure)
# ==========================================

class BankStatementExtraction(BaseModel):
    customer_name: Optional[str] = None
    account_number: Optional[str] = None
    bank_name: Optional[str] = None
    period_from: Optional[str] = None
    period_to: Optional[str] = None
    opening_balance: Optional[float] = None
    closing_balance: Optional[float] = None
    total_credit: Optional[float] = None
    total_debit: Optional[float] = None
    full_transaction_list: List[Dict[str, Any]] = Field(default_factory=list)

class LoanExtraction(BaseModel):
    lender_name: Optional[str] = None
    loan_account_number: Optional[str] = None
    sanction_amount: Optional[float] = None
    interest_rate: Optional[float] = None
    emi_amount: Optional[float] = None
    tenure: Optional[int] = None
    repayment_schedule: List[Dict[str, Any]] = Field(default_factory=list)
    outstanding_balance: Optional[float] = None
    penalty_charges: Optional[float] = None

class BalanceSheetExtraction(BaseModel):
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    net_worth: Optional[float] = None
    current_assets: Optional[float] = None
    current_liabilities: Optional[float] = None

class StockStatementExtraction(BaseModel):
    stock_value: Optional[float] = None
    debtor_value: Optional[float] = None
    creditor_value: Optional[float] = None
    ageing_data: List[Dict[str, Any]] = Field(default_factory=list)
