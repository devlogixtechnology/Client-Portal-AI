"""
LLM Financial Summary & Insight Engine (LIG - Overdue Recovery & Dual-Persona) Package.
"""

from src.llm.dual_persona_engine import DualPersonaInsightEngine
from src.llm.insight_engine import FinancialInsightEngine
from src.llm.ollama_client import OllamaLocalClient
from src.llm.schemas import (
    ClientViewSummary,
    DualPersonaSummaryResult,
    FinancialInsight,
    FinancialSummaryRequest,
    FinancialSummaryResult,
    InsightCategory,
    OverdueAccount,
    OverdueSummaryMetrics,
    PersonaType,
    RiskTier,
    RMViewSummary,
)

__all__ = [
    "FinancialInsightEngine",
    "DualPersonaInsightEngine",
    "OllamaLocalClient",
    "FinancialSummaryRequest",
    "FinancialSummaryResult",
    "DualPersonaSummaryResult",
    "ClientViewSummary",
    "RMViewSummary",
    "OverdueAccount",
    "OverdueSummaryMetrics",
    "FinancialInsight",
    "RiskTier",
    "InsightCategory",
    "PersonaType",
]
