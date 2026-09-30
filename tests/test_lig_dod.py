"""
Definition of Done (DoD) & Acceptance Criteria Verification:
1. Core module fully implemented with zero syntax errors or unhandled exceptions.
2. Automated unit test script passes 100% locally.
3. Execution verified under physical offline network conditions with zero runtime cloud API calls.
4. Latency budget strictly < 500ms.
5. All 5 sample financial statements processed into valid structured insight JSON reports.
"""

import json
from pathlib import Path
from unittest.mock import patch
import pytest

from src.llm.insight_engine import FinancialInsightEngine
from src.pipeline import FinancialIngestionPipeline

SAMPLES = [
    "Sample_1_TechVanguard_FY24.pdf",
    "Sample_2_ApexRetail_FY24.xlsx",
    "Sample_3_BioHealth_Diagnostics_FY24.pdf",
    "Sample_4_PrecisionManufacturing_FY24.xlsx",
    "Sample_5_CleanEnergySolutions_FY24.pdf",
]


def blocked_socket(*args, **kwargs):
    raise RuntimeError("ILLEGAL EXTERNAL NETWORK ACCESS ATTEMPTED IN OFFLINE LIG ENGINE!")


def test_lig_dod_all_five_samples_offline():
    """Verify LIG engine processes all 5 sample statements 100% offline within latency budget."""
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    pipeline = FinancialIngestionPipeline()
    engine = FinancialInsightEngine()

    with patch("socket.socket.connect", side_effect=blocked_socket), \
         patch("socket.create_connection", side_effect=blocked_socket):

        for sample_name in SAMPLES:
            file_path = raw_dir / sample_name
            assert file_path.exists(), f"Sample file missing: {file_path}"

            # 1. Run ingestion
            doc = pipeline.ingest_file(file_path, output_dir=processed_dir)
            assert doc is not None

            # 2. Run LIG Insight Engine
            result = engine.analyze_statement(doc)
            assert result is not None
            assert result.status == "SUCCESS"
            assert result.latency_ms < 500, f"Latency failure: {result.latency_ms}ms >= 500ms for {sample_name}"
            assert len(result.executive_summary) > 20
            assert len(result.overdue_accounts) > 0
            assert result.overdue_metrics.total_overdue_amount >= 0.0

            # 3. Save and verify insights JSON artifact
            insights_file = processed_dir / f"{result.document_id}_insights.json"
            with open(insights_file, "w", encoding="utf-8") as f:
                json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)

            assert insights_file.exists()
            with open(insights_file, "r", encoding="utf-8") as f:
                saved_data = json.load(f)
                assert saved_data["document_id"] == result.document_id
                assert saved_data["status"] == "SUCCESS"
                assert "overdue_metrics" in saved_data
                assert "overdue_accounts" in saved_data
                assert "key_insights" in saved_data
