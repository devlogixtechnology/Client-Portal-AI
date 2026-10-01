"""
CLI Runner for LLM Financial Summary & Insight Engine (LIG - Overdue Recovery, Dual Persona & Accounting Anomaly Engine).
Usage:
    python scripts/run_insight_engine.py --mode anomaly --input-dir data/processed --output-dir data/processed
    python scripts/run_insight_engine.py --mode dual --file data/processed/stmt_sample_1_techvanguard_fy24_structured.json
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.llm.anomaly_engine import AccountingAnomalyEngine
from src.llm.dual_persona_engine import DualPersonaInsightEngine
from src.llm.insight_engine import FinancialInsightEngine
from src.pipeline import FinancialIngestionPipeline


def main():
    parser = argparse.ArgumentParser(description="Run LLM Financial Summary & Insight Engine (LIG - Overdue Recovery, Dual Persona & Anomaly Detection).")
    parser.add_argument("--file", type=str, help="Path to single structured JSON file or raw PDF/XLSX file")
    parser.add_argument("--input-dir", type=str, default="data/processed", help="Directory of processed JSON statements or raw statements")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Directory to save output insight JSON files")
    parser.add_argument("--mode", type=str, choices=["standard", "dual", "anomaly", "all"], default="all", help="Engine execution mode ('standard', 'dual', 'anomaly', 'all')")

    args = parser.parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    json_files = []
    if args.file:
        file_path = Path(args.file)
        json_files = [file_path]
    else:
        input_dir = Path(args.input_dir)
        json_files = sorted(list(input_dir.glob("*_structured.json")))
        if not json_files:
            print(f"No *_structured.json files found in {input_dir}. Running ingestion pipeline first...")
            pipeline = FinancialIngestionPipeline()
            pipeline.ingest_batch(Path("data/raw"), output_dir=input_dir)
            json_files = sorted(list(input_dir.glob("*_structured.json")))

    for file_path in json_files:
        if file_path.suffix.lower() == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                doc_data = json.load(f)
        else:
            pipeline = FinancialIngestionPipeline()
            doc_obj = pipeline.ingest_file(file_path)
            doc_data = doc_obj.model_dump()

        doc_id = doc_data.get("document_id", file_path.stem)

        # 1. Anomaly Mode
        if args.mode in ("anomaly", "all"):
            anomaly_engine = AccountingAnomalyEngine()
            anom_res = anomaly_engine.analyze_anomalies(doc_data)
            out_file = out_dir / f"{doc_id}_anomalies.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(anom_res.model_dump(), f, indent=2, ensure_ascii=False)
            print(f"  * [ANOMALY] {doc_id}: Score={anom_res.overall_risk_score} ({anom_res.overall_health_tier}) - Latency={anom_res.latency_ms:.2f}ms")

        # 2. Dual Persona Mode
        if args.mode in ("dual", "all"):
            dual_engine = DualPersonaInsightEngine()
            dual_res = dual_engine.analyze_dual_persona(doc_data)
            out_file = out_dir / f"{doc_id}_dual_insights.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(dual_res.model_dump(), f, indent=2, ensure_ascii=False)
            print(f"  * [DUAL] {doc_id}: RM Risk={dual_res.rm_view.collection_urgency_tier} - Latency={dual_res.latency_ms:.2f}ms")

        # 3. Standard Overdue Recovery Mode
        if args.mode in ("standard", "all"):
            insight_engine = FinancialInsightEngine()
            std_res = insight_engine.analyze_statement(doc_data)
            out_file = out_dir / f"{doc_id}_insights.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(std_res.model_dump(), f, indent=2, ensure_ascii=False)
            print(f"  * [STANDARD] {doc_id}: Overdue=${std_res.overdue_metrics.total_overdue_amount:,.2f} - Latency={std_res.latency_ms:.2f}ms")

    print(f"\n[COMPLETED] Successfully generated report artifacts in {out_dir}.")


if __name__ == "__main__":
    main()
