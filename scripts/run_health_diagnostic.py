"""
CLI Runner for Master End-to-End Financial Health Diagnostic Test (LIG-4).
Usage:
    python scripts/run_health_diagnostic.py --input-dir data/raw --output-dir data/processed
    python scripts/run_health_diagnostic.py --file data/raw/Sample_1_TechVanguard_FY24.pdf
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.diagnostic.health_diagnostic import FinancialHealthDiagnosticSuite


def main():
    parser = argparse.ArgumentParser(description="Run Master End-to-End Financial Health Diagnostic Test (LIG-4).")
    parser.add_argument("--file", type=str, help="Path to single financial statement file (PDF/XLSX or JSON)")
    parser.add_argument("--input-dir", type=str, default="data/raw", help="Directory of financial statement files")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Directory to save master diagnostic JSON artifacts")

    args = parser.parse_args()
    suite = FinancialHealthDiagnosticSuite()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.file:
        file_path = Path(args.file)
        print(f"Executing master diagnostic suite for file: {file_path}...")
        report = suite.run_diagnostic(file_path)

        out_file = out_dir / f"{report.document_id}_master_diagnostic.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2, ensure_ascii=False)

        print(f"\n=======================================================")
        print(f"[DIAGNOSTIC COMPLETE] Document: {report.document_id}")
        print(f"  - Company: {report.company_name} ({report.fiscal_period})")
        print(f"  - Composite Health Grade: [{report.composite_health_grade}]")
        print(f"  - Total End-to-End Latency: {report.total_latency_ms:.2f}ms")
        print(f"  - Offline Verification: {report.offline_verified} (Zero Cloud API Calls)")
        print(f"-------------------------------------------------------")
        for stage in report.stage_results:
            print(f"  * [{stage.status.upper()}] {stage.stage_name} ({stage.latency_ms:.2f}ms)")
        print(f"=======================================================")
        print(f"Saved Master Report: {out_file}\n")

    else:
        input_dir = Path(args.input_dir)
        print(f"Processing batch master diagnostic suite in {input_dir}...")
        raw_files = sorted([f for f in input_dir.glob("*") if f.suffix.lower() in (".pdf", ".xlsx")])
        if not raw_files:
            print(f"No raw statements found in {input_dir}. Checking processed JSON files...")
            raw_files = sorted(list(input_dir.glob("*_structured.json")))

        reports = []
        for file_path in raw_files:
            report = suite.run_diagnostic(file_path)
            reports.append(report)
            out_file = out_dir / f"{report.document_id}_master_diagnostic.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(report.model_dump(), f, indent=2, ensure_ascii=False)
            print(f"  * [{report.composite_health_grade}] {report.document_id}: Total Latency={report.total_latency_ms:.2f}ms (Offline Verified)")

        print(f"\n[COMPLETED] Master diagnostic reports generated for {len(reports)} documents.")


if __name__ == "__main__":
    main()
