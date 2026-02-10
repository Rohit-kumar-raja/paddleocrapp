import os
import re

# Fix PaddlePaddle 3.3.0 PIR/OneDNN crash on CPU
os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
# Disable model hoster connectivity check
os.environ["DISABLE_MODEL_SOURCE_CHECK"] = "True"

from paddleocr import PaddleOCR
from services.parsers.pan_parser import PANParser
from services.parsers.aadhaar_parser import AadhaarParser

class OCRService:
    def __init__(self):
        # Initialize PaddleOCR
        self.ocr = PaddleOCR(lang="en", use_textline_orientation=True)

    def extract_data(self, image_path: str):
        """
        Extracts raw text and identifies document type, then routes to the correct parser.
        Returns a dictionary with extracted fields and confidence scores.
        """
        try:
            print(f"Running OCR on {image_path}...")
            result = self.ocr.predict(image_path)
            raw_lines = []
            
            for page in result:
                if isinstance(page, dict) and "rec_texts" in page:
                    for text in page.get("rec_texts", []):
                        raw_lines.append(text.strip())
                else:
                    # Handle other possible PaddleOCR return formats if necessary
                    print(f"Unexpected page format: {type(page)}")
            
            print(f"Extracted {len(raw_lines)} lines.")
        except Exception as e:
            print(f"OCR Error during predict: {e}")
            import traceback
            traceback.print_exc()
            raw_lines = []

        parser = self._get_parser(raw_lines)
        if parser:
            data = parser.parse()
        else:
            data = {
                "document_type": "Unknown",
                "document_score": 0.0
            }
        
        data['raw_text'] = raw_lines
        return data

    def _get_parser(self, lines):
        full_text = " ".join(lines).upper()
        
        # Detect PAN
        if "INCOME" in full_text and "TAX" in full_text:
            return PANParser(lines)
        
        # Detect Aadhaar
        if "UIDAI" in full_text or re.search(r"\d{4}\s\d{4}\s\d{4}", full_text):
            return AadhaarParser(lines)
        
        return None
