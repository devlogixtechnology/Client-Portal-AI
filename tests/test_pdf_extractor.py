"""Tests for PDFExtractor using pdfplumber."""
import pytest
from pathlib import Path
from src.extractors.pdf_extractor import PDFExtractor

def test_pdf_extractor_sample_1():
    extractor = PDFExtractor()
    sample_path = Path("data/raw/Sample_1_TechVanguard_FY24.pdf")
    assert sample_path.exists(), "Sample 1 PDF must exist"

    raw_data = extractor.extract(sample_path)
    assert raw_data.company_name == "TechVanguard Software Inc."
    assert raw_data.currency == "USD"
    assert raw_data.unit_multiplier == 1000
    assert len(raw_data.tables) >= 2, "Should extract Balance Sheet and Income Statement tables"
    assert len(raw_data.narrative_sections) >= 1, "Should detect notes section"
    assert "Note 1" in raw_data.raw_text

def test_pdf_extractor_sample_3():
    extractor = PDFExtractor()
    sample_path = Path("data/raw/Sample_3_BioHealth_Diagnostics_FY24.pdf")
    assert sample_path.exists()

    raw_data = extractor.extract(sample_path)
    assert raw_data.company_name == "BioHealth Diagnostics Inc."
    assert raw_data.currency == "GBP"
    assert len(raw_data.tables) >= 2
