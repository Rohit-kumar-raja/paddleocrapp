import re

class BaseParser:
    def __init__(self, raw_lines):
        self.raw_lines = raw_lines
        self.full_text = " ".join(raw_lines).upper()

    def parse(self):
        """Should be implemented by subclasses"""
        raise NotImplementedError

    def is_valid_name(self, text):
        text = text.upper().strip()
        if len(text) < 3 or any(char.isdigit() for char in text):
            return False
        if not re.match(r"^[A-Z\s\.]+$", text):
            return False
        
        invalid_words = [
            "INDIA", "GOVT", "GOVERNMENT", "DOB", "YEAR", "FATHER", "MALE", "FEMALE", 
            "THE", "INCOME", "TAX", "DEPARTMENT", "SIGNATURE", "ADDRESS", "UNIQUE", 
            "IDENTIFICATION", "AUTHORITY", "DEPARTMENT", "REPUBLIC", "VIDYAPEETH"
        ]
        if any(word in text for word in invalid_words):
            return False
        return True

    def calculate_score(self, data, important_fields):
        found_fields = [field for field in important_fields if data.get(field)]
        return len(found_fields) / len(important_fields) if important_fields else 0.0
