import pytest
from fastapi.testclient import TestClient
import time
import json
from models.enums import ExtractType, FinancialDocumentType
from main_api import app

client = TestClient(app)

def test_bank_statement_async_flow():
    # 1. Create a dummy file
    files = {"file": ("test_bank.pdf", b"dummy pdf content", "application/pdf")}
    
    # 2. Form data
    data = {
        "extract_type": ExtractType.BANK_STATEMENT.value,
        "account_name": "TEST ACCOUNT NAME",
        "account_number": "1234567890",
        "bank_name": "TEST BANK",
        "tenure_months": 6
    }
    
    # 3. Post to /extract
    response = client.post("/extract", files=files, data=data)
    assert response.status_code == 200
    res_json = response.json()
    
    assert res_json["api_status"] == "success"
    assert "job_id" in res_json
    job_id = res_json["job_id"]
    
    # 4. Wait a tiny bit for the async job to complete in the background
    # Since background tasks are run after the response is sent, TestClient might need a slight delay
    time.sleep(1)
    
    # 5. Check status
    status_response = client.get(f"/extract/status/{job_id}")
    assert status_response.status_code == 200
    status_json = status_response.json()
    
    # It should be COMPLETED now since our mock processors are very fast
    assert status_json["job_status"] == "completed"
    assert "statement_summary" in status_json
    assert status_json["validation_result"]["account_match_status"] == True

def test_missing_params_for_bank_statement():
    files = {"file": ("test_bank.pdf", b"dummy pdf content", "application/pdf")}
    data = {
        "extract_type": ExtractType.BANK_STATEMENT.value,
        "account_name": "TEST",
        "account_number": "123"
        # missing bank_name and tenure_months
    }
    response = client.post("/extract", files=files, data=data)
    assert response.status_code == 400

def test_loan_statement_async_flow():
    files = {"file": ("test_loan.pdf", b"dummy pdf content", "application/pdf")}
    
    data = {
        "extract_type": ExtractType.LOAN_DOCUMENT.value,
        "account_name": "TEST NAME",
        "account_number": "L1234567890",
        "institute_name": "TEST LENDER BANK",
        "tenure_months": 24
    }
    
    response = client.post("/extract", files=files, data=data)
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    
    time.sleep(1)
    
    status_response = client.get(f"/extract/status/{job_id}")
    assert status_response.status_code == 200
    status_json = status_response.json()
    assert status_json["job_status"] == "completed"
    assert "loan_summary" in status_json
    assert status_json["validation_result"]["institute_match"] == True

def test_financial_document_async_flow():
    files = {"file": ("test_financial.pdf", b"dummy pdf content", "application/pdf")}
    
    data = {
        "extract_type": ExtractType.FINANCIAL_DOCUMENT.value,
        "account_name": "COMPANY XYZ",
        "account_number": "ACC123",
        "institute_name": "BANK ABC",
        "tenure": "FY24",
        "doc_type": FinancialDocumentType.BALANCE_SHEET.value
    }
    
    response = client.post("/extract", files=files, data=data)
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    
    time.sleep(1)
    
    status_response = client.get(f"/extract/status/{job_id}")
    assert status_response.status_code == 200
    status_json = status_response.json()
    assert status_json["job_status"] == "completed"
    assert "financial_metrics" in status_json
    assert "working_capital" in status_json["financial_metrics"]

