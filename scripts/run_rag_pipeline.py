"""
CLI Runner for Data & RAG Pipeline Hardening (DRP - Overdue Recovery).
Usage:
    python scripts/run_rag_pipeline.py --index --input-dir data/processed
    python scripts/run_rag_pipeline.py --query "What are the overdue receivables collection policies?" --company "TechVanguard"
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline import FinancialIngestionPipeline
from src.rag.rag_pipeline import OverdueRAGPipeline


def main():
    parser = argparse.ArgumentParser(description="Run Data & RAG Pipeline Hardening (DRP - Overdue Recovery).")
    parser.add_argument("--index", action="store_true", help="Index all financial statement chunks into the vector store")
    parser.add_argument("--input-dir", type=str, default="data/processed", help="Directory of processed JSON statement files")
    parser.add_argument("--query", type=str, help="Semantic search query text for context retrieval")
    parser.add_argument("--company", type=str, help="Optional company filter for vector search")
    parser.add_argument("--top-k", type=int, default=3, help="Number of top matching chunks to retrieve")

    args = parser.parse_args()
    rag_pipeline = OverdueRAGPipeline()

    if args.index:
        input_dir = Path(args.input_dir)
        print(f"Indexing financial statement chunks from {input_dir}...")

        chunk_files = list(input_dir.glob("*_chunks.json"))
        if not chunk_files:
            print(f"No *_chunks.json files found. Running ingestion pipeline on raw data first...")
            ingestion = FinancialIngestionPipeline()
            ingestion.ingest_batch(Path("data/raw"), output_dir=input_dir)
            chunk_files = list(input_dir.glob("*_chunks.json"))

        total_added = 0
        for chunk_file in sorted(chunk_files):
            added = rag_pipeline.index_processed_chunks_file(chunk_file)
            total_added += added
            print(f"  * Indexed {added} chunks from {chunk_file.name}")

        print(f"\n[COMPLETED] Successfully indexed {total_added} vector chunks into local vector store.")

    if args.query:
        print(f"\nExecuting semantic search query: '{args.query}' (company_filter={args.company}, top_k={args.top_k})...")
        response = rag_pipeline.query(args.query, company_filter=args.company, top_k=args.top_k)

        print(f"=======================================================")
        print(f"[RAG QUERY RESPONSE] Latency: {response.retrieval_latency_ms:.2f}ms | Status: {response.status}")
        print(f"-------------------------------------------------------")
        for idx, match in enumerate(response.retrieved_chunks):
            print(f"Match #{idx+1} [Score: {match.similarity_score:.4f}] - {match.company_name} ({match.note_title}):")
            print(f"  {match.text[:200]}...\n")
        print(f"=======================================================")


if __name__ == "__main__":
    main()
