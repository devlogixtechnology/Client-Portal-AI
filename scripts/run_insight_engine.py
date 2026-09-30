"""
CLI Runner for LLM Financial Summary & Insight Engine (LIG - Overdue Recovery & Dual Persona).
Usage:
    python scripts/run_insight_engine.py --persona dual --input-dir data/processed --output-dir data/processed
    python scripts/run_insight_engine.py --file data/processed/stmt_sample_1_techvanguard_fy24_structured.json
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.llm.dual_persona_engine import DualPersonaInsightEngine
from src.llm.insight_engine import FinancialInsightEngine
from src.pipeline import FinancialIngestionPipeline


def main():
    parser = argparse.ArgumentParser(description="Run LLM Financial Summary & Insight Engine (LIG - Overdue Recovery & Dual Persona).")
    parser.add_argument("--file", type=str, help="Path to single structured JSON file or raw PDF/XLSX file")
    parser.add_argument("--input-dir", type=str, default="data/processed", help="Directory of processed JSON statements or raw statements")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Directory to save output insight JSON files")
    parser.add_argument("--persona", type=str, choices=["standard", "dual"], default="dual", help="Summary persona mode ('standard' or 'dual')")

    args = parser.parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.persona == "dual":
        dual_engine = DualPersonaInsightEngine()

        if args.file:
            file_path = Path(args.file)
            print(f"Generating dual-persona report for single file: {file_path}...")
            if file_path.suffix.lower() == ".json":
                with open(file_path, "r", encoding="utf-8") as f:
                    doc_data = json.load(f)
            else:
                pipeline = FinancialIngestionPipeline()
                doc_obj = pipeline.ingest_file(file_path)
                doc_data = doc_obj.model_dump()

            result = dual_engine.analyze_dual_persona(doc_data)
            out_file = out_dir / f"{result.document_id}_dual_insights.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)

            print(f"[SUCCESS] Dual-persona engine completed in {result.latency_ms:.2f}ms")
            print(f"  - Document ID: {result.document_id}")
            print(f"  - Client Headline: {result.client_view.account_status_headline}")
            print(f"  - RM Risk Urgency: {result.rm_view.collection_urgency_tier}")
            print(f"  - Saved report: {out_file}")

        else:
            input_dir = Path(args.input_dir)
            print(f"Processing batch dual-persona generation in {input_dir}...")
            json_files = list(input_dir.glob("*_structured.json"))
            if not json_files:
                print(f"No *_structured.json files found in {input_dir}. Running ingestion pipeline first...")
                pipeline = FinancialIngestionPipeline()
                pipeline.ingest_batch(Path("data/raw"), output_dir=input_dir)
                json_files = list(input_dir.glob("*_structured.json"))

            for file_path in sorted(json_files):
                with open(file_path, "r", encoding="utf-8") as f:
                    doc_data = json.load(f)
                result = dual_engine.analyze_dual_persona(doc_data)
                out_file = out_dir / f"{result.document_id}_dual_insights.json"
                with open(out_file, "w", encoding="utf-8") as f:
                    json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)
                print(f"  * [{result.status}] {result.document_id}: RM Risk={result.rm_view.collection_urgency_tier} ({result.latency_ms:.2f}ms)")

            print(f"\n[COMPLETED] Generated dual-persona reports for {len(json_files)} documents.")

    else:
        engine = FinancialInsightEngine()

        if args.file:
            file_path = Path(args.file)
            print(f"Generating insight report for single file: {file_path}...")
            if file_path.suffix.lower() == ".json":
                with open(file_path, "r", encoding="utf-8") as f:
                    doc_data = json.load(f)
            else:
                pipeline = FinancialIngestionPipeline()
                doc_obj = pipeline.ingest_file(file_path)
                doc_data = doc_obj.model_dump()

            result = engine.analyze_statement(doc_data)
            out_file = out_dir / f"{result.document_id}_insights.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)

            print(f"[SUCCESS] Insight engine completed in {result.latency_ms:.2f}ms")
            print(f"  - Saved report: {out_file}")

        else:
            input_dir = Path(args.input_dir)
            print(f"Processing batch insight generation in {input_dir}...")
            json_files = list(input_dir.glob("*_structured.json"))
            for file_path in sorted(json_files):
                with open(file_path, "r", encoding="utf-8") as f:
                    doc_data = json.load(f)
                result = engine.analyze_statement(doc_data)
                out_file = out_dir / f"{result.document_id}_insights.json"
                with open(out_file, "w", encoding="utf-8") as f:
                    json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)
                print(f"  * [{result.status}] {result.document_id}: Overdue=${result.overdue_metrics.total_overdue_amount:,.2f} ({result.latency_ms:.2f}ms)")


if __name__ == "__main__":
    main()
