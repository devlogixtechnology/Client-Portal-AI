"""
Unit and Definition of Done (DoD) verification tests for LIG-2 Dual-Persona Summary Engine.
Verifies Client vs. Relationship Manager summary generation, latency < 500ms, and 100% offline execution.
"""

import json
from pathlib import Path
from unittest.mock import patch
import pytest

from src.llm.dual_persona_engine import DualPersonaInsightEngine
from src.llm.schemas import DualPersonaSummaryResult, RiskTier
from src.pipeline import FinancialIngestionPipeline

SAMPLES = [
    "Sample_1_TechVanguard_FY24.pdf",
    "Sample_2_ApexRetail_FY24.xlsx",
    "Sample_3_BioHealth_Diagnostics_FY24.pdf",
    "Sample_4_PrecisionManufacturing_FY24.xlsx",
    "Sample_5_CleanEnergySolutions_FY24.pdf",
]


def blocked_socket(*args, **kwargs):
    raise RuntimeError("ILLEGAL EXTERNAL NETWORK ACCESS ATTEMPTED IN DUAL PERSONA ENGINE!")


def test_dual_persona_engine_execution():
    """Verify DualPersonaInsightEngine returns distinct Client and RM persona summaries."""
    pipeline = FinancialIngestionPipeline()
    sample_file = Path("data/raw/Sample_1_TechVanguard_FY24.pdf")
    doc = pipeline.ingest_file(sample_file)

    engine = DualPersonaInsightEngine()
    result = engine.analyze_dual_persona(doc)

    assert isinstance(result, DualPersonaSummaryResult)
    assert result.document_id == doc.document_id
    assert result.status == "SUCCESS"
    assert result.latency_ms < 500.0, f"Latency {result.latency_ms}ms exceeds 500ms threshold"

    # Client View Assertions
    assert len(result.client_view.executive_summary) > 20
    assert len(result.client_view.settlement_options) >= 2
    assert len(result.client_view.self_service_actions) >= 2
    assert len(result.client_view.reassuring_note) > 10

    # RM View Assertions
    assert len(result.rm_view.internal_risk_assessment) > 20
    assert result.rm_view.collection_urgency_tier in [RiskTier.CRITICAL, RiskTier.HIGH, RiskTier.MEDIUM, RiskTier.LOW]
    assert result.rm_view.recommended_credit_limit > 0
    assert len(result.rm_view.tactical_negotiation_playbook) >= 3


def test_dual_persona_dod_all_five_samples_offline():
    """Verify all 5 sample financial statements generate valid dual persona JSON artifacts offline."""
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    pipeline = FinancialIngestionPipeline()
    engine = DualPersonaInsightEngine()

    with patch("socket.socket.connect", side_effect=blocked_socket), \
         patch("socket.create_connection", side_effect=blocked_socket):

        for sample_name in SAMPLES:
            file_path = raw_dir / sample_name
            assert file_path.exists(), f"Sample missing: {file_path}"

            doc = pipeline.ingest_file(file_path, output_dir=processed_dir)
            result = engine.analyze_dual_persona(doc)

            assert result.status == "SUCCESS"
            assert result.latency_ms < 500.0, f"Latency failure: {result.latency_ms}ms >= 500ms"

            out_file = processed_dir / f"{result.document_id}_dual_insights.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)

            assert out_file.exists()
            with open(out_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                assert "client_view" in data
                assert "rm_view" in data
                assert data["client_view"]["account_status_headline"] != ""
                assert len(data["rm_view"]["tactical_negotiation_playbook"]) > 0
