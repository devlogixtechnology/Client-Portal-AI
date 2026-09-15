"""
CLI Runner for Client Portal AI Financial Statement Ingestion Pipeline.
Usage:
    python scripts/run_ingestion.py --input-dir data/raw --output-dir data/processed
    python scripts/run_ingestion.py --file data/raw/Sample_1_TechVanguard_FY24.pdf --output-dir data/processed
"""

import argparse
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline import FinancialIngestionPipeline


def main():
    parser = argparse.ArgumentParser(description="Ingest financial statements into structured JSON and RAG chunks.")
    parser.add_argument("--file", type=str, help="Path to single financial statement (PDF/XLSX)")
    parser.add_argument("--input-dir", type=str, default="data/raw", help="Directory of financial statements")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Directory to save output JSON files")

    args = parser.parse_args()
    pipeline = FinancialIngestionPipeline()
    output_path = Path(args.output_dir)

    if args.file:
        file_path = Path(args.file)
        print(f"Processing single file: {file_path}...")
        doc = pipeline.ingest_file(file_path, output_dir=output_path)
        print(f"[SUCCESS] Ingested {file_path.name}")
        print(f"  - Normalized line items: {len(doc.line_items)}")
        print(f"  - Notes chunks: {len(doc.notes_chunks)}")
        print(f"  - Summary metrics: {doc.summary_metrics}")
    else:
        input_path = Path(args.input_dir)
        print(f"Processing batch in {input_path} -> {output_path}...")
        docs = pipeline.ingest_batch(input_path, output_dir=output_path)
        print(f"\n[COMPLETED] Batch ingestion completed for {len(docs)} documents.")
        for d in docs:
            print(f"  * {d.metadata.source_file}: {len(d.line_items)} line items, {len(d.notes_chunks)} chunks")


if __name__ == "__main__":
    main()
