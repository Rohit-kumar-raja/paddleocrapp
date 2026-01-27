import os
import re
from paddleocr import PaddleOCR
from services.parsers.pan_parser import PANParser
from services.parsers.aadhaar_parser import AadhaarParser

# Disable model hoster connectivity check
os.environ["DISABLE_MODEL_SOURCE_CHECK"] = "True"

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
            result = self.ocr.predict(image_path)
            raw_lines = []
            
            for page in result:
                for text in page.get("rec_texts", []):
                    raw_lines.append(text.strip())
        except Exception as e:
            print(f"OCR Error: {e}")
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

