from typing import Dict, Any, Tuple
from models.schemas import JobResultResponse, BalanceSheetExtraction, StockStatementExtraction
from models.enums import APIStatus, JobStatus, FinancialDocumentType
from services.statement_service import BaseExtractionService
from utils.api_logger import log_external_call

class FinancialStatementService(BaseExtractionService):
    
    @log_external_call("FinancialStatementService", "extract")
    def extract(self, file_path: str, request_data: Dict[str, Any]) -> Any:
        """
        Mock extraction for Company Financial Document (Balance Sheet or Stock Statement).
        """
        doc_type = request_data.get("doc_type")
        
        if doc_type == FinancialDocumentType.BALANCE_SHEET:
            return BalanceSheetExtraction(
                total_assets=500000.0,
                total_liabilities=200000.0,
                net_worth=300000.0,
                current_assets=150000.0,
                current_liabilities=50000.0
            )
        elif doc_type == FinancialDocumentType.STOCK_STATEMENT:
            return StockStatementExtraction(
                stock_value=120000.0,
                debtor_value=80000.0,
                creditor_value=40000.0,
                ageing_data=[
                    {"days": "0-30", "amount": 50000.0},
                    {"days": "31-60", "amount": 20000.0},
                    {"days": "61-90", "amount": 10000.0}
                ]
            )
        else:
            raise ValueError(f"Unknown financial document type: {doc_type}")

    def validate(self, extracted: Any, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Match specific string logic here for validation requirements.
        Note: We just mock a basic validation here since the requirements say "institute_match" and "document_period_match"
        """
        doc_period_match = True # Mocking this as we'd need date logic
        inst_match = True # Mocking as we didn't extract the institute name in the schema for financials but the spec requires it.
        
        return {
            "document_period_match": doc_period_match,
            "institute_match": inst_match
        }

    def compute(self, extracted: Any, validation: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Computes various business logic rules.
        """
        summary = {}
        risk = {}
        
        if isinstance(extracted, BalanceSheetExtraction):
            working_capital = (extracted.current_assets or 0) - (extracted.current_liabilities or 0)
            current_ratio = (extracted.current_assets or 0) / (extracted.current_liabilities or 1)
            summary = {
                "working_capital": working_capital,
                "current_ratio": round(current_ratio, 2)
            }
            if current_ratio < 1.0:
                 summary["liquidity_flag"] = "Low Liquidity"
            else:
                 summary["liquidity_flag"] = "Healthy Liquidity"
                 
        elif isinstance(extracted, StockStatementExtraction):
            dp_estimation_candidate = (extracted.stock_value or 0) + (extracted.debtor_value or 0) - (extracted.creditor_value or 0)
            summary = {
                "dp_estimation_candidate": dp_estimation_candidate
            }
             
        return summary, risk

    def build_response(self, validation: Dict[str, Any], summary: Dict[str, Any], risk: Dict[str, Any]) -> JobResultResponse:
        return JobResultResponse(
            api_status=APIStatus.SUCCESS,
            job_status=JobStatus.COMPLETED,
            validation_result=validation,
            financial_metrics=summary
        )
