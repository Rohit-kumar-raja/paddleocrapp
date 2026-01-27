import re
from services.parsers.base_parser import BaseParser

class AadhaarParser(BaseParser):
    def parse(self):
        data = {
            "document_type": "Aadhaar Card",
            "name": None,
            "dob": None,
            "gender": None,
            "id_number": None,
            "document_score": 0.0
        }

        dob_index = -1
        for i, line in enumerate(self.raw_lines):
            line_up = line.upper().strip()
            
            # Aadhaar Number
            if not data["id_number"]:
                match = re.search(r"\b\d{4}\s\d{4}\s\d{4}\b", line)
                if match:
                    data["id_number"] = match.group(0)
            
            # DOB
            if not data["dob"]:
                match = re.search(r"DOB[:\s]*(\d{2}/\d{2}/\d{4})", line_up) or re.search(r"(\d{2}/\d{2}/\d{4})", line)
                if match:
                    data["dob"] = match.group(1) if len(match.groups()) > 0 else match.group(0)
                    dob_index = i
            
            # Gender
            if not data["gender"]:
                if "FEMALE" in line_up:
                    data["gender"] = "Female"
                elif "MALE" in line_up:
                    data["gender"] = "Male"

        # Name Extraction (Above DOB)
        if dob_index != -1:
            for offset in range(1, 4):
                idx = dob_index - offset
                if idx >= 0 and self.is_valid_name(self.raw_lines[idx]):
                    data["name"] = self.raw_lines[idx].upper()
                    break
        
        # Fallback for name
        if not data["name"]:
            for line in self.raw_lines:
                if self.is_valid_name(line):
                    data["name"] = line.upper()
                    break

        data["document_score"] = self.calculate_score(data, ["name", "dob", "id_number"])
        return data
