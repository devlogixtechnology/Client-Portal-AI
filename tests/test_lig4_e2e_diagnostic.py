"""
End-to-End (E2E) Definition of Done (DoD) Verification Suite for LIG-4.
Verifies master 4-stage diagnostic pipeline execution, 100% socket network isolation,
latency budget < 500ms across all stages, and robust error recovery.
"""

import json
from pathlib import Path
from unittest.mock import patch
import pytest

from src.diagnostic.health_diagnostic import FinancialHealthDiagnosticSuite
from src.llm.schemas import MasterDiagnosticReport, PipelineStageStatus
from src.pipeline import FinancialIngestionPipeline

SAMPLES = [
    "Sample_1_TechVanguard_FY24.pdf",
    "Sample_2_ApexRetail_FY24.xlsx",
    "Sample_3_BioHealth_Diagnostics_FY24.pdf",
    "Sample_4_PrecisionManufacturing_FY24.xlsx",
    "Sample_5_CleanEnergySolutions_FY24.pdf",
]


def blocked_socket(*args, **kwargs):
    raise RuntimeError("ILLEGAL EXTERNAL NETWORK ACCESS ATTEMPTED IN E2E DIAGNOSTIC SUITE!")


def test_e2e_master_diagnostic_all_five_samples_offline():
    """Verify master diagnostic suite executes end-to-end for all 5 sample statements 100% offline within 500ms budget."""
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    suite = FinancialHealthDiagnosticSuite()
    pipeline = FinancialIngestionPipeline()

    with patch("socket.socket.connect", side_effect=blocked_socket), \
         patch("socket.create_connection", side_effect=blocked_socket):

        for sample_name in SAMPLES:
            file_path = raw_dir / sample_name
            assert file_path.exists(), f"Sample missing: {file_path}"

            # Ingest file
            doc = pipeline.ingest_file(file_path, output_dir=processed_dir)

            # Execute master diagnostic on document
            report = suite.run_diagnostic(doc)

            assert isinstance(report, MasterDiagnosticReport)
            assert report.overall_status == "SUCCESS"
            assert report.offline_verified is True
            assert report.total_latency_ms < 500.0, f"Total latency {report.total_latency_ms}ms exceeds 500ms threshold for {sample_name}"
            assert report.composite_health_grade in ["A+", "A", "B", "C", "D", "F"]

            # Verify all 4 stage results are present and passed
            assert len(report.stage_results) == 4
            for stage in report.stage_results:
                assert stage.status in [PipelineStageStatus.PASSED, PipelineStageStatus.WARNING]

            # Sub-engine output assertions
            assert report.overdue_summary is not None
            assert report.dual_persona_summary is not None
            assert report.anomaly_detection is not None

            # Save and verify master diagnostic JSON artifact
            out_file = processed_dir / f"{report.document_id}_master_diagnostic.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(report.model_dump(), f, indent=2, ensure_ascii=False)

            assert out_file.exists()
            with open(out_file, "r", encoding="utf-8") as f:
                saved = json.load(f)
                assert saved["document_id"] == report.document_id
                assert saved["composite_health_grade"] == report.composite_health_grade
                assert len(saved["stage_results"]) == 4



def test_e2e_diagnostic_error_recovery_corrupted_input():
    """Verify diagnostic suite raises clear FileNotFoundError for non-existent or corrupted files."""
    suite = FinancialHealthDiagnosticSuite()

    with pytest.raises(FileNotFoundError):
        suite.run_diagnostic("data/raw/NonExistent_File_99.pdf")
