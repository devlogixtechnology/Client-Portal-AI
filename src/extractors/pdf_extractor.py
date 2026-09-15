"""
PDF Financial Statement Extractor using pdfplumber.
Extracts structured tables (Balance Sheet, Income Statement) and narrative text (Notes to Accounts).
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import pdfplumber

from src.extractors.base import BaseExtractor
from src.models import ExtractedRawData


class PDFExtractor(BaseExtractor):
    """Extracts tables, narrative sections, and metadata from financial statement PDFs."""

    def extract(self, file_path: Path) -> ExtractedRawData:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        all_tables: List[List[List[Any]]] = []
        narrative_sections: List[Dict[str, str]] = []
        full_text_pages: List[str] = []

        company_name: Optional[str] = None
        fiscal_period: Optional[str] = None
        currency: str = "USD"
        unit_multiplier: int = 1

        with pdfplumber.open(file_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                full_text_pages.append(page_text)

                # Detect metadata on early pages
                if page_idx == 0:
                    lines = [ln.strip() for ln in page_text.splitlines() if ln.strip()]
                    if lines:
                        company_name = lines[0]
                    currency = self.detect_currency(page_text)
                    unit_mult, _ = self.detect_unit_multiplier(page_text)
                    unit_multiplier = unit_mult
                    detected_period = self.detect_fiscal_period(page_text)
                    if detected_period != "FY":
                        fiscal_period = detected_period

                # Extract tables with explicit table settings
                tables = page.extract_tables()
                if tables:
                    for tbl in tables:
                        # Clean table rows: filter out all-empty rows
                        cleaned_tbl = []
                        for row in tbl:
                            if any(cell is not None and str(cell).strip() for cell in row):
                                cleaned_row = [str(c).strip() if c is not None else "" for c in row]
                                cleaned_tbl.append(cleaned_row)
                        if len(cleaned_tbl) >= 2:
                            all_tables.append(cleaned_tbl)

                # Check if page is predominantly notes/narrative
                # If page has 'Note ' or 'NOTES TO' and either no table or table is small footnote
                if re.search(r"\b(?:NOTES TO|Note\s+\d+|Summary of Significant Accounting Policies)\b", page_text, re.IGNORECASE):
                    # Separate narrative from page
                    narrative_sections.append({
                        "page": str(page_idx + 1),
                        "title": f"Notes Section (Page {page_idx + 1})",
                        "text": page_text
                    })

        full_raw_text = "\n\n--- PAGE BREAK ---\n\n".join(full_text_pages)

        # Fallback company name from filename if not cleanly parsed
        if not company_name or len(company_name) > 60:
            clean_stem = file_path.stem.replace("_", " ").replace("-", " ")
            company_name = clean_stem.split("FY")[0].strip()

        if not fiscal_period:
            fiscal_period = self.detect_fiscal_period(file_path.name)

        return ExtractedRawData(
            company_name=company_name,
            fiscal_period=fiscal_period,
            currency=currency,
            unit_multiplier=unit_multiplier,
            tables=all_tables,
            narrative_sections=narrative_sections,
            raw_text=full_raw_text,
            source_file=file_path.name,
            file_type="pdf"
        )
