"""
Unit tests for LIG-1 Local Quantized LLM Setup (Offline Ollama Llama-3.2).
Verifies offline model config resolution, timeout bounds, and local fallback handling.
"""

from pathlib import Path
import pytest

from src.llm.ollama_client import OllamaLocalClient
from src.llm.schemas import (
    FinancialInsight,
    FinancialSummaryResult,
    InsightCategory,
    OverdueAccount,
    OverdueSummaryMetrics,
    RiskTier,
)


def test_offline_config_file_exists():
    """Verify that offline model configuration file exists pre-cached under ./models/."""
    config_path = Path("models/ollama_llama3.2_config.json")
    assert config_path.exists(), "Offline model configuration file must exist in ./models/"


def test_ollama_client_initialization_and_fallback():
    """Verify Ollama client initialization and deterministic offline execution fallback."""
    client = OllamaLocalClient()
    assert client.config is not None
    assert client.config.get("offline_mode") is True

    result = client.generate("Test prompt for local model execution")
    assert result is not None
    assert "status" in result
    assert "latency_ms" in result
    assert result["latency_ms"] < 500.0, "Local inference or fallback must execute within 500ms budget"


def test_pydantic_schemas_validation():
    """Verify strongly-typed Pydantic v2 data contract schemas."""
    account = OverdueAccount(
        account_id="INV-001",
        client_name="Test Corp",
        overdue_amount=15000.0,
        currency="USD",
        days_overdue=45,
        risk_tier=RiskTier.HIGH,
        recommended_action="Send formal payment notice",
        recovery_probability=0.8
    )
    assert account.overdue_amount == 15000.0
    assert account.risk_tier == RiskTier.HIGH

    metrics = OverdueSummaryMetrics(
        total_receivables=100000.0,
        total_overdue_amount=15000.0,
        overdue_ratio=0.15,
        critical_overdue_count=1,
        average_days_overdue=45.0,
        expected_recovery_amount=12000.0
    )
    assert metrics.overdue_ratio == 0.15

    insight = FinancialInsight(
        insight_id="INS-001",
        category=InsightCategory.OVERDUE_RECOVERY,
        title="Test Overdue Insight",
        description="Detailed description of overdue receivables",
        impact_score=0.9,
        actionable_recommendation="Take action immediately"
    )
    assert insight.category == InsightCategory.OVERDUE_RECOVERY
