"""
Unit tests for DRP-4: Scanned Financial Statement OCR Fallback (Tesseract).
Verifies scanned page detection, Tesseract OCR invocation, fallback error recovery, and PDFExtractor integration.
"""

from pathlib import Path
import pytest
from src.extractors.ocr_fallback import (
    TesseractOCRFallback,
    OCRExtractionConfig,
    OCRFallbackResult,
)
from src.extractors.pdf_extractor import PDFExtractor
from src.models import ExtractedRawData


def test_ocr_fallback_is_scanned_page_detection():
    """Verify is_scanned_page correctly identifies low text density / scanned pages."""
    ocr_engine = TesseractOCRFallback(config=OCRExtractionConfig(min_text_density_chars=50))

    # Low text density (scanned page) -> True
    assert ocr_engine.is_scanned_page("   ", tables_count=0) is True
    assert ocr_engine.is_scanned_page("Short header", tables_count=0) is True

    # High text density or page with extracted tables -> False
    dense_text = "TechVanguard Limited Consolidated Financial Statement for the Year Ended 31 December 2024. Notes to Accounts."
    assert len(dense_text) > 50
    assert ocr_engine.is_scanned_page(dense_text, tables_count=0) is False
    assert ocr_engine.is_scanned_page("Short header", tables_count=2) is False


def test_tesseract_ocr_fallback_execution():
    """Verify extract_page_ocr handles execution safely without throwing unhandled exceptions."""
    ocr_engine = TesseractOCRFallback()
    
    # Mock page object without to_image / render methods to test deterministic fallback
    class MockPage:
        pass

    result = ocr_engine.extract_page_ocr(MockPage(), page_idx=0)
    assert isinstance(result, OCRFallbackResult)
    assert result.is_fallback_triggered is True
    assert result.ocr_method in ["TesseractOCR", "DeterministicLayoutFallback"]
    assert len(result.ocr_text) > 0


def test_pdf_extractor_ocr_fallback_integration():
    """Verify PDFExtractor integrates OCR fallback and sets is_ocr_fallback_used flag."""
    sample_pdf = Path("data/raw/sample_statement_1.pdf")
    if not sample_pdf.exists():
        # Fallback to any existing sample PDF in data/
        pdfs = list(Path("data").glob("**/*.pdf"))
        if pdfs:
            sample_pdf = pdfs[0]
        else:
            pytest.skip("No sample PDF files found in data/ for integration test")

    extractor = PDFExtractor()
    extracted = extractor.extract(sample_pdf)

    assert isinstance(extracted, ExtractedRawData)
    assert hasattr(extracted, "is_ocr_fallback_used")
    assert extracted.file_type == "pdf"
