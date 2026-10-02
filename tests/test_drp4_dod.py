"""
Definition of Done (DoD) automated test suite for DRP-4: Scanned Financial Statement OCR Fallback (Tesseract).
Validates socket-level offline isolation, scanned PDF detection, OCR fallback flag tagging, sub-2000ms latency,
and error recovery.
"""

import socket
import time
from pathlib import Path
import pytest

from src.extractors.ocr_fallback import (
    TesseractOCRFallback,
    OCRExtractionConfig,
    OCRFallbackResult,
)
from src.extractors.pdf_extractor import PDFExtractor
from src.models import ExtractedRawData


@pytest.fixture(autouse=True)
def block_network():
    """Guard fixture enforcing 100% offline network isolation by blocking outbound socket connections."""
    original_socket = socket.socket

    def guard_socket(*args, **kwargs):
        raise RuntimeError("NETWORK ATTEMPT DETECTED: DRP-4 must run 100% offline without network socket calls!")

    socket.socket = guard_socket
    yield
    socket.socket = original_socket


def test_drp4_ocr_fallback_dod_offline():
    """
    DoD Test: DRP-4 OCR Fallback Execution & Offline Integrity.
    - Process sample financial PDFs.
    - Test OCR fallback trigger on low-density pages.
    - Assert 100% offline execution without network calls.
    - Assert ExtractedRawData schema integrity and latency budget < 2000ms.
    """
    raw_dir = Path("data/raw")
    pdf_files = list(raw_dir.glob("*.pdf"))
    if not pdf_files:
        pdf_files = list(Path("data").glob("**/*.pdf"))
    assert len(pdf_files) > 0, "Expected at least one PDF file under data/ for DRP-4 DoD test"

    # Configure PDFExtractor with custom high threshold to force OCR fallback trigger for test validation
    forced_ocr_config = OCRExtractionConfig(min_text_density_chars=5000)
    extractor = PDFExtractor(ocr_config=forced_ocr_config)

    for pdf_file in pdf_files[:3]:
        t0 = time.perf_counter()
        extracted = extractor.extract(pdf_file)
        latency_ms = (time.perf_counter() - t0) * 1000

        # Assertions
        assert isinstance(extracted, ExtractedRawData)
        assert extracted.is_ocr_fallback_used is True, f"Expected OCR fallback to be triggered for {pdf_file.name}"
        assert extracted.source_file == pdf_file.name
        assert latency_ms < 2000.0, f"Extraction latency limit exceeded: {latency_ms:.2f}ms > 2000ms target"


def test_drp4_ocr_fallback_error_recovery_dod():
    """DoD Test: Verify OCR fallback error recovery on corrupted/invalid page objects."""
    ocr_engine = TesseractOCRFallback()
    
    # Passing None or invalid object must return OCRFallbackResult with error_message set, never crash
    result = ocr_engine.extract_page_ocr(None, page_idx=0)
    assert isinstance(result, OCRFallbackResult)
    assert result.is_fallback_triggered is True
    assert result.ocr_method == "DeterministicLayoutFallback"
    assert result.error_message is not None
