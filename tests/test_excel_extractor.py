"""Tests for ExcelExtractor using openpyxl."""
import pytest
from pathlib import Path
from src.extractors.excel_extractor import ExcelExtractor

def test_excel_extractor_sample_2():
    extractor = ExcelExtractor()
    sample_path = Path("data/raw/Sample_2_ApexRetail_FY24.xlsx")
    assert sample_path.exists(), "Sample 2 XLSX must exist"

    raw_data = extractor.extract(sample_path)
    assert "Apex Retail" in (raw_data.company_name or "")
    assert len(raw_data.tables) >= 2, "Should extract Balance Sheet and Income Statement sheets"
    assert len(raw_data.narrative_sections) >= 1, "Should extract Notes sheet"

def test_excel_extractor_sample_4():
    extractor = ExcelExtractor()
    sample_path = Path("data/raw/Sample_4_PrecisionManufacturing_FY24.xlsx")
    assert sample_path.exists()

    raw_data = extractor.extract(sample_path)
    assert raw_data.currency == "EUR"
    assert len(raw_data.tables) >= 2
