import re
from services.parsers.base_parser import BaseParser

class PANParser(BaseParser):
    def parse(self):
        data = {
            "document_type": "PAN Card",
            "name": None,
            "dob": None,
            "father_name": None,
            "id_number": None,
            "document_score": 0.0
        }

        for i, line in enumerate(self.raw_lines):
            line_up = line.upper().strip()
            
            # PAN Number
            if not data["id_number"]:
                match = re.search(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", line_up)
                if match:
                    data["id_number"] = match.group(0)
            
            # DOB
            if not data["dob"]:
                match = re.search(r"\d{2}/\d{2}/\d{4}", line)
                if match:
                    data["dob"] = match.group(0)

            # Name Extraction Logic
            if any(key in line_up for key in ["INCOME", "TAX", "DEPARTMENT"]):
                # Look for name below the header
                for offset in range(1, 4):
                    if i + offset < len(self.raw_lines):
                        candidate = self.raw_lines[i + offset]
                        if self.is_valid_name(candidate):
                            data["name"] = candidate.upper()
                            break
                if data["name"]: continue

        data["document_score"] = self.calculate_score(data, ["name", "dob", "id_number"])
        return data
