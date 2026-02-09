import json
from services.table_service import TableExtractionService

def test_table_extraction():
    print("Initializing TableExtractionService...")
    service = TableExtractionService()
    
    file_path = "statement.pdf"
    columns = ["Date", "Description", "Balance"]
    
    print(f"Extracting table from {file_path} with columns {columns}...")
    try:
        data = service.extract_table_data(file_path, columns)
        print("Extraction successful!")
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Extraction failed: {e}")

if __name__ == "__main__":
    test_table_extraction()
