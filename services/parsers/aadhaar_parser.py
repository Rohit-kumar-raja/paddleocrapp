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
            "father_name": None,
            "address": None,
            "document_score": 0.0
        }

        dob_index = -1
        address_index = -1
        
        for i, line in enumerate(self.raw_lines):
            line_up = line.upper().strip()
            
            # Aadhaar Number
            if not data["id_number"]:
                match = re.search(r"\b\d{4}\s\d{4}\s\d{4}\b", line)
                if match:
                    data["id_number"] = match.group(0)
            
            # DOB - Prioritize lines containing "DOB"
            match = re.search(r"DOB[:\s]*(\d{2}/\d{2}/\d{4})", line_up)
            if match:
                data["dob"] = match.group(1)
                dob_index = i
            elif not data["dob"]:
                match = re.search(r"(\d{2}/\d{2}/\d{4})", line)
                if match:
                    data["dob"] = match.group(0)
                    dob_index = i
            
            # Gender
            if not data["gender"]:
                if "FEMALE" in line_up:
                    data["gender"] = "Female"
                elif "MALE" in line_up:
                    data["gender"] = "Male"

            # Father/Husband Name
            if not data["father_name"]:
                # Match S/O, D/O, W/O or Father:
                f_match = re.search(r"(?:S/O|D/O|W/O|FATHER)\s*[:]?\s*([A-Z\s\.\u0080-\uf8ff]+)", line_up)
                if f_match:
                    name_part = f_match.group(1).strip()
                    name_part = re.split(r"[,;]", name_part)[0].strip()
                    if len(name_part) > 3:
                        data["father_name"] = name_part

            # Address Detection (Take first occurrences commonly seen on Aadhaar cards)
            if "ADDRESS" in line_up and address_index == -1:
                # Avoid metadata labels like "English Address"
                if "ENGLISH" not in line_up and "TYPE" not in line_up:
                    address_index = i
                    match = re.search(r"ADDRESS[:\s]*(.+)", line, re.IGNORECASE)
                    if match and len(match.group(1).strip()) > 3:
                        remainder = match.group(1).strip()
                        if not any(k in remainder.upper() for k in ["MOBILE", "TEL", "PHONE"]):
                            data["address"] = remainder

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

        # Address Extraction (Merge following lines)
        if address_index != -1:
            address_parts = []
            if data["address"]: address_parts.append(data["address"])
            
            for j in range(address_index + 1, min(address_index + 15, len(self.raw_lines))):
                line = self.raw_lines[j].strip()
                line_up = line.upper()
                
                # Stop if we hit 12-digit Aadhaar number pattern (usually at the bottom)
                # But only if it's NOT the same as the current id_number? No, usually any 12 digit block on bottom is a stop signal.
                if re.search(r"\b\d{4}\s\d{4}\s\d{4}\b", line): break
                
                # Skip known junk keywords
                if any(k in line_up for k in ["WWW.", "HTTP", "HELP@", "UIDAI", "DATE:", "UNIQUE", "MOBILE", "TEL", "PHONE"]): 
                    continue
                
                if line and len(line) > 2:
                    cleaned_line = line
                    
                    # Handle S/O Name, Address line
                    if any(k in line_up for k in ["S/O", "D/O", "W/O"]):
                        # Extract part after the first comma
                        parts = re.split(r",", line, 1)
                        if len(parts) > 1:
                            potential_addr = parts[1].strip()
                            if len(potential_addr) > 2:
                                cleaned_line = potential_addr
                            else:
                                continue
                        else:
                            continue
                    
                    # Skip common junk like "Mobile No:" without number which might be missed by keyword filter
                    if re.match(r"^MOBILE\s*NO\s*[:]?\s*$", line_up): continue

                    # Avoid duplicates and metadata
                    if data["name"] and line_up == data["name"]: continue
                    if cleaned_line not in address_parts:
                        address_parts.append(cleaned_line)

            if address_parts:
                data["address"] = ", ".join(address_parts)

        data["document_score"] = self.calculate_score(data, ["name", "dob", "id_number", "address"])
        return data
