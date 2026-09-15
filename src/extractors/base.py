"""
Base extractor interface and text/number parsing utilities.
"""

import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, List, Optional, Tuple

from src.models import ExtractedRawData


class BaseExtractor(ABC):
    """Abstract base extractor for financial documents."""

    @abstractmethod
    def extract(self, file_path: Path) -> ExtractedRawData:
        """Extract raw tables, text, and metadata from the document."""
        pass

    @staticmethod
    def clean_numeric_str(val: Any) -> Tuple[Optional[float], str]:
        """
        Cleans a string or numeric cell into a float and original string representation.
        Handles negative numbers formatted as (1,234.56), currency symbols ($£€),
        dashes/nils ('-', '—'), and comma separators.
        """
        if val is None:
            return None, ""
        
        # If already float or int
        if isinstance(val, (int, float)):
            return float(val), str(val)

        raw_str = str(val).strip()
        if not raw_str:
            return None, ""

        # Check for dash / nil
        if raw_str in ("-", "—", "–", "N/A", "nil", "None"):
            return 0.0, raw_str

        # Remove currency symbols and clean spaces
        cleaned = re.sub(r"[\$€£¥\s]", "", raw_str)

        # Check for parentheses indicating negative: e.g. (1,234)
        is_negative = False
        paren_match = re.match(r"^\((.*?)\)$", cleaned)
        if paren_match:
            is_negative = True
            cleaned = paren_match.group(1).strip()
        elif cleaned.startswith("-"):
            is_negative = True
            cleaned = cleaned[1:].strip()

        # Remove comma thousands separators
        cleaned = cleaned.replace(",", "")

        try:
            val_float = float(cleaned)
            if is_negative:
                val_float = -val_float
            return val_float, raw_str
        except ValueError:
            return None, raw_str

    @staticmethod
    def detect_currency(text: str) -> str:
        """Detects reported currency from header text."""
        lower = text.lower()
        if "£" in text or "gbp" in lower or "pounds" in lower:
            return "GBP"
        if "€" in text or "eur" in lower or "euro" in lower:
            return "EUR"
        if "cad" in lower or "c$" in text:
            return "CAD"
        if "aud" in lower or "a$" in text:
            return "AUD"
        if "jpy" in lower or "yen" in lower or "¥" in text:
            return "JPY"
        return "USD"

    @staticmethod
    def detect_unit_multiplier(text: str) -> Tuple[int, str]:
        """Detects unit scale (in thousands, in millions, etc.)."""
        lower = text.lower()
        if "in millions" in lower or "(millions)" in lower or "()" in lower:
            return 1000000, "millions"
        if "in thousands" in lower or "(thousands)" in lower or "()" in lower or "('000)" in lower or "in " in lower:
            return 1000, "thousands"
        return 1, "exact"

    @staticmethod
    def detect_fiscal_period(text: str) -> str:
        """Detects fiscal year or period (e.g. FY2024, 2024, Dec 31, 2024)."""
        # Match explicit FY pattern: FY2024, FY 2024, FY24
        fy_match = re.search(r"\b(?:FY|Fiscal Year)\s*(20\d{2}|\d{2})\b", text, re.IGNORECASE)
        if fy_match:
            yr = fy_match.group(1)
            if len(yr) == 2:
                yr = f"20{yr}"
            return f"FY{yr}"

        # Match Year pattern e.g. 'December 31, 2024' or 'ended 31 December 2024'
        ended_match = re.search(r"(?:ended|as of|at)\s+([A-Za-z]+ \d{1,2},? (20\d{2}))", text, re.IGNORECASE)
        if ended_match:
            return ended_match.group(2)

        # Year match
        year_match = re.search(r"\b(20\d{2})\b", text)
        if year_match:
            return year_match.group(1)

        return "FY"
