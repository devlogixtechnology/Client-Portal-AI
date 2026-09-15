"""Definition of Done (DoD) Verification:
Asserts that all 5 sample financial statements are parsed into structured JSON
and chunked text ready for offline RAG embedding.
"""
import json
import pytest
from pathlib import Path
from src.pipeline import FinancialIngestionPipeline

SAMPLES = [
    "Sample_1_TechVanguard_FY24.pdf",
    "Sample_2_ApexRetail_FY24.xlsx",
    "Sample_3_BioHealth_Diagnostics_FY24.pdf",
    "Sample_4_PrecisionManufacturing_FY24.xlsx",
    "Sample_5_CleanEnergySolutions_FY24.pdf",
]

def test_pipeline_dod_all_five_samples():
    pipeline = FinancialIngestionPipeline()
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    assert raw_dir.exists(), "Raw data directory must exist"

    results = []
    for sample_name in SAMPLES:
        file_path = raw_dir / sample_name
        assert file_path.exists(), f"Sample file must exist: {file_path}"

        doc = pipeline.ingest_file(file_path, output_dir=processed_dir)
        results.append(doc)

        # 1. Verify structured JSON was created and is valid
        structured_file = processed_dir / f"{doc.document_id}_structured.json"
        assert structured_file.exists(), f"Structured JSON missing for {sample_name}"
        with open(structured_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["document_id"] == doc.document_id
            assert "metadata" in data
            assert len(data["line_items"]) > 10, f"Must have parsed line items for {sample_name}"
            assert len(data["notes_chunks"]) >= 1, f"Must have parsed note chunks for {sample_name}"
            assert "revenue" in data["summary_metrics"]

        # 2. Verify chunks JSON was created and formatted for RAG
        chunks_file = processed_dir / f"{doc.document_id}_chunks.json"
        assert chunks_file.exists(), f"Chunks JSON missing for {sample_name}"
        with open(chunks_file, "r", encoding="utf-8") as f:
            chunks = json.load(f)
            assert len(chunks) >= 1
            for c in chunks:
                assert "chunk_id" in c
                assert "text" in c
                assert "metadata" in c
                assert "estimated_tokens" in c
                assert c["metadata"]["type"] == "notes_to_accounts"

    assert len(results) == 5, "Definition of Done requires exactly 5 sample statements processed"
