"""
Unit and Definition of Done (DoD) verification tests for AccountingAnomalyEngine (LIG-3).
Verifies balance sheet anomaly detection, footnote audit trigger keywords, latency < 500ms, and 100% offline socket isolation.
"""

import json
from pathlib import Path
from unittest.mock import patch
import pytest

from src.llm.anomaly_engine import AccountingAnomalyEngine
from src.llm.schemas import AnomalyCategory, AnomalyDetectionResult, AnomalySeverity
from src.pipeline import FinancialIngestionPipeline

SAMPLES = [
    "Sample_1_TechVanguard_FY24.pdf",
    "Sample_2_ApexRetail_FY24.xlsx",
    "Sample_3_BioHealth_Diagnostics_FY24.pdf",
    "Sample_4_PrecisionManufacturing_FY24.xlsx",
    "Sample_5_CleanEnergySolutions_FY24.pdf",
]


def blocked_socket(*args, **kwargs):
    raise RuntimeError("ILLEGAL EXTERNAL NETWORK ACCESS ATTEMPTED IN ANOMALY ENGINE!")


def test_anomaly_engine_ratios_and_execution():
    """Verify ratio calculations and anomaly reporting for ingested financial statement."""
    pipeline = FinancialIngestionPipeline()
    sample_file = Path("data/raw/Sample_1_TechVanguard_FY24.pdf")
    doc = pipeline.ingest_file(sample_file)

    engine = AccountingAnomalyEngine()
    result = engine.analyze_anomalies(doc)

    assert isinstance(result, AnomalyDetectionResult)
    assert result.document_id == doc.document_id
    assert result.status == "SUCCESS"
    assert result.latency_ms < 500.0, f"Latency {result.latency_ms}ms exceeds 500ms threshold"

    # Liquidity Metrics Assertions
    assert result.liquidity_metrics.current_ratio is not None
    assert result.liquidity_metrics.quick_ratio is not None
    assert result.liquidity_metrics.working_capital is not None
    assert result.liquidity_metrics.dso_days is not None

    # Risk Score & Health Tier Assertions
    assert 0.0 <= result.overall_risk_score <= 100.0
    assert result.overall_health_tier in ["HEALTHY", "MODERATE_RISK", "HIGH_RISK", "CRITICAL_STRESS"]


def test_footnote_audit_keyword_detection():
    """Verify footnote keyword scanning detects audit warning trigger phrases."""
    sample_data = {
        "document_id": "stmt_test_going_concern",
        "company_name": "Stressed Corp",
        "fiscal_period": "FY24",
        "summary_metrics": {"revenue": 500000.0, "total_assets": 400000.0, "total_liabilities": 450000.0},
        "notes_chunks": [
            {"text": "Note 1: The company has experienced operating losses that raise substantial doubt about its ability to continue as a going concern."}
        ]
    }

    engine = AccountingAnomalyEngine()
    result = engine.analyze_anomalies(sample_data)

    assert result.overall_risk_score > 30.0
    audit_anomalies = [a for a in result.anomalies if a.category == AnomalyCategory.AUDIT_FOOTNOTE_FLAG]
    assert len(audit_anomalies) >= 1
    assert audit_anomalies[0].severity == AnomalySeverity.CRITICAL
    assert "Going Concern" in audit_anomalies[0].title


def test_anomaly_engine_dod_all_five_samples_offline():
    """Verify all 5 sample financial statements generate valid anomaly JSON reports offline."""
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    pipeline = FinancialIngestionPipeline()
    engine = AccountingAnomalyEngine()

    with patch("socket.socket.connect", side_effect=blocked_socket), \
         patch("socket.create_connection", side_effect=blocked_socket):

        for sample_name in SAMPLES:
            file_path = raw_dir / sample_name
            assert file_path.exists(), f"Sample missing: {file_path}"

            doc = pipeline.ingest_file(file_path, output_dir=processed_dir)
            result = engine.analyze_anomalies(doc)

            assert result.status == "SUCCESS"
            assert result.latency_ms < 500.0, f"Latency failure: {result.latency_ms}ms >= 500ms"

            out_file = processed_dir / f"{result.document_id}_anomalies.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)

            assert out_file.exists()
            with open(out_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                assert "liquidity_metrics" in data
                assert "anomalies" in data
                assert "overall_risk_score" in data
                assert "overall_health_tier" in data
