import os
import re
import json

# -------- IMPORTANT: Disable model hoster connectivity check --------
os.environ["DISABLE_MODEL_SOURCE_CHECK"] = "True"

from paddleocr import PaddleOCR


class IdentityCardScanner:
    def __init__(self):
        print("Loading PaddleOCR Model... (CPU mode)")

        self.ocr = PaddleOCR(
            lang="en",
            use_textline_orientation=True
        )

    # ---------------- OCR ----------------
    def extract_text(self, image_path):
        if not os.path.exists(image_path):
            return []

        try:
            result = self.ocr.predict(image_path)
            lines = []

            for page in result:
                for text in page.get("rec_texts", []):
                    lines.append(text.strip())

            return lines

        except Exception as e:
            print("OCR Error:", e)
            return []

    # ---------------- VALIDATORS ----------------
    def is_valid_name(self, text):
        text = text.upper().strip()

        if len(text) < 3:
            return False

        if any(char.isdigit() for char in text):
            return False

        if not re.match(r"^[A-Z\s\.]+$", text):
            return False

        invalid_words = [
            "INDIA", "GOVT", "GOVERNMENT", "DOB", "YEAR",
            "FATHER", "MALE", "FEMALE", "THE", "INCOME",
            "TAX", "DEPARTMENT", "SIGNATURE", "ADDRESS",
            "UNIQUE", "IDENTIFICATION", "AUTHORITY"
        ]

        for word in invalid_words:
            if word in text:
                return False

        return True

    # ---------------- MAIN PARSER ----------------
    def parse_document(self, image_path):
        raw_lines = self.extract_text(image_path)

        data = {
            "document_type": "Unknown",
            "name": None,
            "dob": None,
            "father_name": None,
            "gender": None,
            "id_number": None,
            "raw_text": raw_lines
        }

        full_text = " ".join(raw_lines).upper()

        # ---------- Detect PAN ----------
        if "INCOME" in full_text and "TAX" in full_text:
            data["document_type"] = "PAN Card"
            self._process_pan(raw_lines, data)

        # ---------- Detect Aadhaar ----------
        elif (
            "UIDAI" in full_text
            or re.search(r"\d{4}\s\d{4}\s\d{4}", full_text)
        ):
            data["document_type"] = "Aadhaar Card"
            self._process_aadhaar(raw_lines, data)

        return data

    # ---------------- PAN LOGIC ----------------
    def _process_pan(self, lines, data):
        # PAN Number
        for line in lines:
            match = re.search(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", line.upper())
            if match:
                data["id_number"] = match.group(0)
                break

        # DOB
        for line in lines:
            match = re.search(r"\d{2}/\d{2}/\d{4}", line)
            if match:
                data["dob"] = match.group(0)
                break

        # Name (after INCOME TAX header)
        for i, line in enumerate(lines):
            clean = line.upper()
            if "INCOME" in clean or "DEPARTMENT" in clean:
                for offset in range(1, 4):
                    if i + offset < len(lines):
                        candidate = lines[i + offset]
                        if self.is_valid_name(candidate):
                            data["name"] = candidate.upper()
                            return

    # ---------------- AADHAAR LOGIC ----------------
    def _process_aadhaar(self, lines, data):
        dob_index = -1

        for i, line in enumerate(lines):
            clean = line.upper()

            # Aadhaar Number
            match = re.search(r"\b\d{4}\s\d{4}\s\d{4}\b", line)
            if match:
                data["id_number"] = match.group(0)

            # DOB
            match = re.search(r"\d{2}/\d{2}/\d{4}", line)
            if match:
                data["dob"] = match.group(0)
                dob_index = i

            # Gender
            if "FEMALE" in clean:
                data["gender"] = "Female"
            elif "MALE" in clean:
                data["gender"] = "Male"

        # Name (1–3 lines above DOB)
        if dob_index != -1:
            for offset in range(1, 4):
                idx = dob_index - offset
                if idx >= 0 and self.is_valid_name(lines[idx]):
                    data["name"] = lines[idx].upper()
                    break


# ---------------- RUN ----------------
if __name__ == "__main__":
    scanner = IdentityCardScanner()

    image_file = "image1.png"
    print(f"Processing {image_file}...")

    result = scanner.parse_document(image_file)
    print(json.dumps(result, indent=4))
