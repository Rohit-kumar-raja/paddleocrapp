from typing import Dict, Any, Tuple
from models.schemas import JobResultResponse, BankStatementExtraction
from models.enums import APIStatus, JobStatus
from services.statement_service import BaseExtractionService
from utils.api_logger import log_external_call

class BankStatementService(BaseExtractionService):
    
    @log_external_call("BankStatementService", "extract")
    def extract(self, file_path: str, request_data: Dict[str, Any]) -> BankStatementExtraction:
        """
        Mock extraction of OCR/LLM mapping for a bank statement.
        In reality, you'd call an LLM with the text extracted via PaddleOCR.
        """
        # Mocking an extracted response.
        return BankStatementExtraction(
            customer_name="TEST ACCOUNT NAME",
            account_number="1234567890",
            bank_name="TEST BANK",
            period_from="2024-01-01",
            period_to="2024-06-30",
            opening_balance=1000.0,
            closing_balance=1500.0,
            total_credit=5000.0,
            total_debit=4500.0,
            full_transaction_list=[
                {"date": "2024-01-05", "description": "Salary", "credit": 5000.0, "debit": 0.0, "balance": 6000.0},
                {"date": "2024-01-10", "description": "Rent", "credit": 0.0, "debit": 4500.0, "balance": 1500.0}
            ]
        )

    def validate(self, extracted: BankStatementExtraction, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Match specific string logic here for validation requirements.
        """
        # Case insensitive simple checking for this mock
        acc_name_match = request.get("account_name", "").lower() in (extracted.customer_name or "").lower()
        acc_num_match = request.get("account_number", "") == extracted.account_number
        bank_match = request.get("bank_name", "").lower() in (extracted.bank_name or "").lower()
        
        # Tenure logic mocking
        declared_tenure = request.get("tenure_months", 6)
        # Mock derived tenure vs declared
        actual_tenure = 6 # derived from period_from and period_to in a real app
        tenure_match = declared_tenure == actual_tenure

        return {
            "account_match_status": acc_name_match and acc_num_match,
            "tenure_match_status": tenure_match,
            "bank_match_status": bank_match
        }

    def compute(self, extracted: BankStatementExtraction, validation: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Computes various business logic rules.
        """
        # Simple computation based on the spec
        avg_monthly_credit = (extracted.total_credit or 0) / 6
        avg_monthly_debit = (extracted.total_debit or 0) / 6
        salary_detected = True if "Salary" in [tx.get("description", "") for tx in extracted.full_transaction_list] else False
        
        summary = {
            "avg_monthly_credit": round(avg_monthly_credit, 2),
            "avg_monthly_debit": round(avg_monthly_debit, 2),
            "salary_detected": salary_detected,
            "salary_tenure_months": 6 if salary_detected else 0,
            "emi_total": 0.0,
            "bounce_charges_count": 0,
            "penalty_total": 0.0,
            "overdraft_days": 0,
            "cash_deposit_ratio": 0.1
        }
        
        risk = {
            "income_stability_score": 85 if salary_detected else 50,
            "banking_behaviour_score": 90,
            "risk_flags": ["No recent overdrafts", "Steady income"] if salary_detected else ["Inconsistent income"]
        }

        return summary, risk

    def build_response(self, validation: Dict[str, Any], summary: Dict[str, Any], risk: Dict[str, Any]) -> JobResultResponse:
        return JobResultResponse(
            api_status=APIStatus.SUCCESS,
            job_status=JobStatus.COMPLETED,
            validation_result=validation,
            statement_summary=summary,
            risk_analysis=risk
        )
