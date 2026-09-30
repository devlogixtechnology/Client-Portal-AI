"""
Unit tests for FinancialInsightEngine (LIG - Overdue Recovery).
Verifies parsing of ingested documents, overdue account aging, and summary generation.
"""

from pathlib import Path
import pytest

from src.llm.insight_engine import FinancialInsightEngine
from src.llm.schemas import FinancialSummaryResult, RiskTier
from src.pipeline import FinancialIngestionPipeline


def test_insight_engine_single_sample_execution():
    """Verify insight engine processes an ingested statement document correctly."""
    pipeline = FinancialIngestionPipeline()
    sample_file = Path("data/raw/Sample_1_TechVanguard_FY24.pdf")
    doc = pipeline.ingest_file(sample_file)

    engine = FinancialInsightEngine()
    result = engine.analyze_statement(doc)

    assert isinstance(result, FinancialSummaryResult)
    assert result.document_id == doc.document_id
    assert result.status == "SUCCESS"
    assert result.latency_ms < 500, f"Latency {result.latency_ms}ms exceeds 500ms threshold"
    assert len(result.overdue_accounts) > 0
    assert result.overdue_metrics.total_overdue_amount > 0
    assert len(result.key_insights) >= 2
    assert len(result.executive_summary) > 50


def test_insight_engine_dict_input():
    """Verify insight engine accepts structured dictionary inputs."""
    raw_dict = {
        "document_id": "stmt_test_corp",
        "company_name": "Test Corp Inc",
        "fiscal_period": "FY24",
        "summary_metrics": {
            "revenue": 5000000.0,
            "gross_profit": 3500000.0,
            "net_income": 800000.0
        },
        "notes_chunks": []
    }

    engine = FinancialInsightEngine()
    result = engine.analyze_statement(raw_dict)

    assert result.document_id == "stmt_test_corp"
    assert result.company_name == "Test Corp Inc"
    assert result.overdue_metrics.total_receivables > 0
    assert result.status == "SUCCESS"
    assert result.latency_ms < 500
