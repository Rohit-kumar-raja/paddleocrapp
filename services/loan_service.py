from typing import Dict, Any, Tuple
from models.schemas import JobResultResponse, LoanExtraction
from models.enums import APIStatus, JobStatus
from services.statement_service import BaseExtractionService
from utils.api_logger import log_external_call

class LoanStatementService(BaseExtractionService):
    
    @log_external_call("LoanStatementService", "extract")
    def extract(self, file_path: str, request_data: Dict[str, Any]) -> LoanExtraction:
        """
        Mock extraction for Loan Statement.
        """
        return LoanExtraction(
            lender_name="TEST LENDER BANK",
            loan_account_number="L1234567890",
            sanction_amount=100000.0,
            interest_rate=8.5,
            emi_amount=5000.0,
            tenure=24,
            outstanding_balance=60000.0,
            penalty_charges=0.0,
            repayment_schedule=[
                {"date": "2024-01-05", "emi": 5000.0, "paid": True, "days_past_due": 0},
                {"date": "2024-02-05", "emi": 5000.0, "paid": False, "days_past_due": 15}
            ]
        )

    def validate(self, extracted: LoanExtraction, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Match specific string logic here for validation requirements.
        """
        loan_acc_match = request.get("account_number", "") == extracted.loan_account_number
        inst_match = request.get("institute_name", "").lower() in (extracted.lender_name or "").lower()
        tenure_match = request.get("tenure_months", 24) == extracted.tenure
        
        # Consistent EMI checks
        emi_consistency = len(set([tx.get("emi", 0) for tx in extracted.repayment_schedule])) <= 1

        return {
            "loan_account_match": loan_acc_match,
            "institute_match": inst_match,
            "tenure_match": tenure_match,
            "emi_consistency": emi_consistency
        }

    def compute(self, extracted: LoanExtraction, validation: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Computes various business logic rules.
        """
        emi_paid = sum(1 for tx in extracted.repayment_schedule if tx.get("paid"))
        emi_missed = sum(1 for tx in extracted.repayment_schedule if not tx.get("paid"))
        
        dpd_list = [tx.get("days_past_due", 0) for tx in extracted.repayment_schedule]
        max_dpd = max(dpd_list) if dpd_list else 0
        
        delinquency_flag = max_dpd > 30

        summary = {
            "emi_paid_count": emi_paid,
            "emi_missed_count": emi_missed,
            "delinquency_flag": delinquency_flag,
            "days_past_due": max_dpd,
            "repayment_discipline_score": max(0, 100 - (emi_missed * 10) - (max_dpd))
        }
        
        risk = {
            "high_risk": delinquency_flag,
            "risk_score": 80 if not delinquency_flag else 30
        }

        return summary, risk

    def build_response(self, validation: Dict[str, Any], summary: Dict[str, Any], risk: Dict[str, Any]) -> JobResultResponse:
        return JobResultResponse(
            api_status=APIStatus.SUCCESS,
            job_status=JobStatus.COMPLETED,
            validation_result=validation,
            loan_summary=summary,
            risk_indicators=risk
        )
