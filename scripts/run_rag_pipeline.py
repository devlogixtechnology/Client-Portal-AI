"""
CLI Runner for Data & RAG Pipeline Hardening (DRP - Overdue Recovery, ChromaDB & Multi-Tenant Isolation).
Usage:
    python scripts/run_rag_pipeline.py --tenant-id tenant_techvanguard --query "What are the overdue accounts recovery policies?"
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline import FinancialIngestionPipeline
from src.rag.chroma_store import ChromaOfflineVectorStore
from src.rag.rag_pipeline import OverdueRAGPipeline
from src.rag.schemas import TenantContext, VectorChunk


def main():
    parser = argparse.ArgumentParser(description="Run Data & RAG Pipeline Hardening (DRP - Overdue Recovery & Multi-Tenant Data Isolation).")
    parser.add_argument("--store", type=str, choices=["local", "chroma"], default="chroma", help="Vector store implementation ('local' or 'chroma')")
    parser.add_argument("--index", action="store_true", help="Index all financial statement chunks into vector store")
    parser.add_argument("--input-dir", type=str, default="data/processed", help="Directory of processed JSON statement files")
    parser.add_argument("--query", type=str, help="Semantic search query text for context retrieval")
    parser.add_argument("--tenant-id", type=str, help="Client tenant ID scope for multi-tenant data isolation")
    parser.add_argument("--company", type=str, help="Optional company filter for vector search")
    parser.add_argument("--top-k", type=int, default=3, help="Number of top matching chunks to retrieve")

    args = parser.parse_args()
    rag_pipeline = OverdueRAGPipeline()

    if args.index:
        input_dir = Path(args.input_dir)
        print(f"Indexing financial statement chunks into {args.store} vector store from {input_dir}...")
        chunk_files = list(input_dir.glob("*_chunks.json"))
        if not chunk_files:
            print(f"No *_chunks.json files found. Running ingestion pipeline on raw data first...")
            ingestion = FinancialIngestionPipeline()
            ingestion.ingest_batch(Path("data/raw"), output_dir=input_dir)
            chunk_files = list(input_dir.glob("*_chunks.json"))

        total_added = 0
        for chunk_file in sorted(chunk_files):
            added = rag_pipeline.index_processed_chunks_file(chunk_file, tenant_id=args.tenant_id)
            total_added += added
            print(f"  * Indexed {added} chunks from {chunk_file.name}")

        print(f"\n[COMPLETED] Successfully indexed {total_added} vector chunks into local vector store.")

    if args.query:
        if args.tenant_id:
            ctx = TenantContext(
                tenant_id=args.tenant_id,
                client_name=args.company or "Client Entity",
                user_role="analyst"
            )
            print(f"\nExecuting tenant-isolated RAG query for tenant '{args.tenant_id}': '{args.query}'...")
            res = rag_pipeline.query_tenant_isolated(args.query, tenant_context=ctx, top_k=args.top_k)

            print(f"=======================================================")
            print(f"[MULTI-TENANT RAG RESPONSE] Tenant: {res.tenant_id} | Latency: {res.retrieval_latency_ms:.2f}ms")
            print(f"Zero Cross-Tenant Leakage: {not res.cross_tenant_leakage_detected}")
            print(f"-------------------------------------------------------")
            for idx, match in enumerate(res.retrieved_chunks):
                print(f"Match #{idx+1} [Tenant: {match.tenant_id} | Score: {match.similarity_score:.4f}] - {match.company_name} ({match.note_title}):")
                print(f"  {match.text[:200]}...\n")
            print(f"=======================================================")

        else:
            print(f"\nExecuting semantic search query: '{args.query}' (company_filter={args.company})...")
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
