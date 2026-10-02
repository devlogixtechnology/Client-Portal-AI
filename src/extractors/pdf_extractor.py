"""
PDF Financial Statement Extractor using pdfplumber and Tesseract OCR Fallback (DRP-4).
Extracts structured tables (Balance Sheet, Income Statement) and narrative text (Notes to Accounts).
Automatically triggers Tesseract OCR fallback when digital text density is below threshold.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import pdfplumber

from src.extractors.base import BaseExtractor
from src.extractors.ocr_fallback import TesseractOCRFallback, OCRExtractionConfig
from src.models import ExtractedRawData


class PDFExtractor(BaseExtractor):
    """Extracts tables, narrative sections, and metadata from financial statement PDFs with OCR fallback."""

    def __init__(
        self,
        ocr_fallback: Optional[TesseractOCRFallback] = None,
        ocr_config: Optional[OCRExtractionConfig] = None
    ):
        self.ocr_fallback = ocr_fallback or TesseractOCRFallback(config=ocr_config)

    def extract(self, file_path: Path) -> ExtractedRawData:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        all_tables: List[List[List[Any]]] = []
        narrative_sections: List[Dict[str, str]] = []
        full_text_pages: List[str] = []
        is_ocr_fallback_used = False

        company_name: Optional[str] = None
        fiscal_period: Optional[str] = None
        currency: str = "USD"
        unit_multiplier: int = 1

        with pdfplumber.open(file_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                page_text = page.extract_text() or ""
                tables = page.extract_tables() or []

                # Low text density or scanned image page -> Trigger OCR Fallback
                if self.ocr_fallback.is_scanned_page(page_text, len(tables)):
                    ocr_result = self.ocr_fallback.extract_page_ocr(page, page_idx)
                    page_text = ocr_result.ocr_text
                    is_ocr_fallback_used = True

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
                if re.search(r"\b(?:NOTES TO|Note\s+\d+|Summary of Significant Accounting Policies|Notes Section)\b", page_text, re.IGNORECASE) or is_ocr_fallback_used:
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
            file_type="pdf",
            is_ocr_fallback_used=is_ocr_fallback_used
        )
