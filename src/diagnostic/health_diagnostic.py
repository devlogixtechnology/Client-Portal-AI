"""
Master End-to-End Financial Health Diagnostic Suite (LIG-4) for LedgerLense.
Orchestrates 4-stage pipeline diagnostic verification combining Document Ingestion (DRP-1),
Overdue Recovery Analytics (LIG-1), Dual-Persona Views (LIG-2), and Accounting Anomaly Detection (LIG-3).
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional

from src.llm.anomaly_engine import AccountingAnomalyEngine
from src.llm.dual_persona_engine import DualPersonaInsightEngine
from src.llm.insight_engine import FinancialInsightEngine
from src.llm.schemas import (
    MasterDiagnosticReport,
    PipelineStageStatus,
    StageDiagnosticResult,
)
from src.models import FinancialStatementDocument
from src.pipeline import FinancialIngestionPipeline

logger = logging.getLogger(__name__)


class FinancialHealthDiagnosticSuite:
    """Master Diagnostic Orchestrator for End-to-End Financial Pipeline Verification."""

    def __init__(self):
        self.ingestion_pipeline = FinancialIngestionPipeline()
        self.insight_engine = FinancialInsightEngine()
        self.dual_engine = DualPersonaInsightEngine()
        self.anomaly_engine = AccountingAnomalyEngine()

    def run_diagnostic(
        self,
        target: Path | str | FinancialStatementDocument | Dict[str, Any]
    ) -> MasterDiagnosticReport:
        """
        Executes end-to-end 4-stage diagnostic test on a target document or raw statement file.
        Returns a MasterDiagnosticReport containing stage results, health grades, and full engine outputs.
        """
        total_start = time.perf_counter()
        stage_results: List[StageDiagnosticResult] = []

        # Stage 1: Document Ingestion & Extraction (DRP-1)
        s1_start = time.perf_counter()
        if isinstance(target, (str, Path)):
            file_path = Path(target)
            if not file_path.exists():
                raise FileNotFoundError(f"Target financial statement file not found: {file_path}")
            if file_path.suffix.lower() == ".json":
                with open(file_path, "r", encoding="utf-8") as f:
                    doc = json.load(f)
            else:
                doc = self.ingestion_pipeline.ingest_file(file_path)
        elif isinstance(target, FinancialStatementDocument):
            doc = target
        else:
            # Handle dictionary payload
            doc = target


        s1_latency = (time.perf_counter() - s1_start) * 1000

        doc_dict = doc.model_dump() if isinstance(doc, FinancialStatementDocument) else doc
        doc_id = doc_dict.get("document_id", "stmt_unknown")
        meta = doc_dict.get("metadata", {})
        company_name = meta.get("company_name", doc_dict.get("company_name", "Unknown Corp"))
        fiscal_period = meta.get("fiscal_period", doc_dict.get("fiscal_period", "FY24"))
        items_count = len(doc_dict.get("line_items", []))

        stage_results.append(
            StageDiagnosticResult(
                stage_name="Stage 1: Document Ingestion & Line Item Taxonomy Normalization",
                status=PipelineStageStatus.PASSED if items_count > 0 else PipelineStageStatus.WARNING,
                latency_ms=round(s1_latency, 2),
                items_processed=items_count,
                warnings=[] if items_count > 0 else ["No line items parsed from raw input"]
            )
        )

        # Stage 2: Overdue Receivables & Insight Engine (LIG-1)
        s2_start = time.perf_counter()
        insight_res = self.insight_engine.analyze_statement(doc)
        s2_latency = (time.perf_counter() - s2_start) * 1000

        stage_results.append(
            StageDiagnosticResult(
                stage_name="Stage 2: LLM Overdue Recovery & Insight Engine",
                status=PipelineStageStatus.PASSED if insight_res.status == "SUCCESS" else PipelineStageStatus.WARNING,
                latency_ms=round(s2_latency, 2),
                items_processed=len(insight_res.overdue_accounts),
                warnings=[]
            )
        )

        # Stage 3: Dual-Persona Summary Engine (LIG-2)
        s3_start = time.perf_counter()
        dual_res = self.dual_engine.analyze_dual_persona(doc)
        s3_latency = (time.perf_counter() - s3_start) * 1000

        stage_results.append(
            StageDiagnosticResult(
                stage_name="Stage 3: Dual-Persona View Summary Engine (Client vs RM)",
                status=PipelineStageStatus.PASSED if dual_res.status == "SUCCESS" else PipelineStageStatus.WARNING,
                latency_ms=round(s3_latency, 2),
                items_processed=2,
                warnings=[]
            )
        )

        # Stage 4: Accounting Anomaly & Liquidity Flag Engine (LIG-3)
        s4_start = time.perf_counter()
        anomaly_res = self.anomaly_engine.analyze_anomalies(doc)
        s4_latency = (time.perf_counter() - s4_start) * 1000

        stage_results.append(
            StageDiagnosticResult(
                stage_name="Stage 4: Accounting Anomaly & Liquidity Stress Engine",
                status=PipelineStageStatus.PASSED if anomaly_res.status == "SUCCESS" else PipelineStageStatus.WARNING,
                latency_ms=round(s4_latency, 2),
                items_processed=len(anomaly_res.anomalies),
                warnings=[f"Detected {len(anomaly_res.anomalies)} anomaly flags"] if len(anomaly_res.anomalies) > 0 else []
            )
        )

        total_latency = (time.perf_counter() - total_start) * 1000

        # Calculate Composite Health Letter Grade
        grade = self._calculate_composite_grade(insight_res, anomaly_res)

        return MasterDiagnosticReport(
            document_id=doc_id,
            company_name=company_name,
            fiscal_period=fiscal_period,
            composite_health_grade=grade,
            stage_results=stage_results,
            overdue_summary=insight_res,
            dual_persona_summary=dual_res,
            anomaly_detection=anomaly_res,
            overall_status="SUCCESS",
            total_latency_ms=round(total_latency, 2),
            offline_verified=True,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    def _calculate_composite_grade(self, insight_res: Any, anomaly_res: Any) -> str:
        """Calculates composite financial health grade (A+, A, B, C, D, F)."""
        risk_score = anomaly_res.overall_risk_score
        overdue_ratio = insight_res.overdue_metrics.overdue_ratio

        if risk_score < 15.0 and overdue_ratio < 0.10:
            return "A+"
        elif risk_score < 35.0 and overdue_ratio < 0.20:
            return "A"
        elif risk_score < 50.0 and overdue_ratio < 0.30:
            return "B"
        elif risk_score < 65.0:
            return "C"
        elif risk_score < 80.0:
            return "D"
        else:
            return "F"
