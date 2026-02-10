import re
from difflib import SequenceMatcher


class MatchingService:
    """Compares user-provided data against OCR-extracted data and returns match scores."""

    # ---------- Name Matching ----------
    @staticmethod
    def match_name(extracted: str, provided: str) -> float:
        """
        Fuzzy name match. Returns 0.0–1.0.
        Normalizes both strings: uppercase, strip extra spaces/punctuation.
        """
        if not extracted or not provided:
            return 0.0

        def normalize(name):
            name = name.upper().strip()
            name = re.sub(r"[^A-Z\s]", "", name)   # keep only letters + spaces
            name = re.sub(r"\s+", " ", name)         # collapse whitespace
            return name

        a = normalize(extracted)
        b = normalize(provided)

        if not a or not b:
            return 0.0

        return round(SequenceMatcher(None, a, b).ratio(), 2)

    # ---------- DOB Matching ----------
    @staticmethod
    def match_dob(extracted: str, provided: str) -> float:
        """
        Exact DOB match after stripping whitespace.
        Both should be in DD/MM/YYYY format.
        Returns 1.0 for match, 0.0 otherwise.
        """
        if not extracted or not provided:
            return 0.0

        def normalize_date(d):
            d = d.strip()
            # Try to handle both DD/MM/YYYY and DD-MM-YYYY
            d = d.replace("-", "/")
            return d

        return 1.0 if normalize_date(extracted) == normalize_date(provided) else 0.0

    # ---------- Address Matching ----------
    @staticmethod
    def match_address(extracted: str, provided: str) -> float:
        """
        Keyword overlap based address matching. Returns 0.0–1.0.
        Splits both into words, calculates overlap ratio.
        """
        if not extracted or not provided:
            return 0.0

        def tokenize(text):
            text = text.upper().strip()
            text = re.sub(r"[^A-Z0-9\s]", " ", text)
            tokens = set(text.split())
            # Remove very short tokens (noise)
            return {t for t in tokens if len(t) > 1}

        extracted_tokens = tokenize(extracted)
        provided_tokens = tokenize(provided)

        if not provided_tokens:
            return 0.0

        overlap = extracted_tokens & provided_tokens
        # Score = what fraction of provided tokens were found in extracted
        score = len(overlap) / len(provided_tokens)
        return round(min(score, 1.0), 2)

    # ---------- Overall Score ----------
    @staticmethod
    def calculate_overall_score(scores: dict) -> float:
        """
        Weighted average of all provided match scores.
        Weights: name=0.3, dob=0.2, address=0.2, photo=0.3
        Only counts fields that were actually provided (non-None).
        """
        weights = {
            "name_match": 0.3,
            "dob_match": 0.2,
            "address_match": 0.2,
            "photo_match": 0.3,
        }

        total_weight = 0.0
        weighted_sum = 0.0

        for key, weight in weights.items():
            if key in scores and scores[key] is not None:
                weighted_sum += scores[key] * weight
                total_weight += weight

        if total_weight == 0:
            return 0.0

        return round(weighted_sum / total_weight, 2)
