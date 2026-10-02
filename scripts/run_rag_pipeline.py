"""
CLI Runner for Data & RAG Pipeline Hardening (DRP - Overdue Recovery & ChromaDB Setup).
Usage:
    python scripts/run_rag_pipeline.py --store chroma --index --input-dir data/processed
    python scripts/run_rag_pipeline.py --store chroma --query "What are the overdue receivables collection policies?" --company "TechVanguard"
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
from src.rag.schemas import VectorChunk


def main():
    parser = argparse.ArgumentParser(description="Run Data & RAG Pipeline Hardening (DRP - Overdue Recovery & ChromaDB Setup).")
    parser.add_argument("--store", type=str, choices=["local", "chroma"], default="chroma", help="Vector store implementation ('local' or 'chroma')")
    parser.add_argument("--index", action="store_true", help="Index all financial statement chunks into the vector store")
    parser.add_argument("--input-dir", type=str, default="data/processed", help="Directory of processed JSON statement files")
    parser.add_argument("--query", type=str, help="Semantic search query text for context retrieval")
    parser.add_argument("--company", type=str, help="Optional company filter for vector search")
    parser.add_argument("--top-k", type=int, default=3, help="Number of top matching chunks to retrieve")

    args = parser.parse_args()

    if args.store == "chroma":
        chroma_store = ChromaOfflineVectorStore()

        if args.index:
            input_dir = Path(args.input_dir)
            print(f"Indexing financial statement chunks into persistent ChromaDB from {input_dir}...")
            chunk_files = list(input_dir.glob("*_chunks.json"))
            if not chunk_files:
                print(f"No *_chunks.json files found. Running ingestion pipeline on raw data first...")
                ingestion = FinancialIngestionPipeline()
                ingestion.ingest_batch(Path("data/raw"), output_dir=input_dir)
                chunk_files = list(input_dir.glob("*_chunks.json"))

            all_chunks = []
            for chunk_file in sorted(chunk_files):
                with open(chunk_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                stmt_id = chunk_file.stem.replace("_chunks", "")
                company_name = stmt_id.replace("stmt_sample_", "").replace("_", " ").title()

                for idx, item in enumerate(data):
                    text = item.get("text", "")
                    if text:
                        all_chunks.append(
                            VectorChunk(
                                chunk_id=item.get("chunk_id", f"{stmt_id}_c{idx}"),
                                statement_id=stmt_id,
                                company_name=company_name,
                                note_title=item.get("note_title", "Notes to Accounts"),
                                text=text,
                                estimated_tokens=item.get("estimated_tokens", len(text) // 4),
                                metadata=item.get("metadata", {})
                            )
                        )

            res = chroma_store.add_chunks(all_chunks)
            print(f"\n[COMPLETED] ChromaDB collection '{res.collection_name}' status: {res.status} ({res.latency_ms:.2f}ms)")
            print(f"Total documents indexed in collection: {res.total_documents}")

        if args.query:
            print(f"\nExecuting ChromaDB semantic query: '{args.query}' (company_filter={args.company}, top_k={args.top_k})...")
            matches = chroma_store.query_similar(args.query, company_filter=args.company, top_k=args.top_k)
            print(f"=======================================================")
            print(f"[CHROMADB QUERY RESPONSE] Retrieved {len(matches)} matching documents:")
            print(f"-------------------------------------------------------")
            for idx, match in enumerate(matches):
                print(f"Match #{idx+1} [Similarity: {match.similarity_score:.4f} | Distance: {match.distance:.4f}] - {match.company_name} ({match.note_title}):")
                print(f"  {match.text[:200]}...\n")
            print(f"=======================================================")

    else:
        rag_pipeline = OverdueRAGPipeline()

        if args.index:
            input_dir = Path(args.input_dir)
            print(f"Indexing financial statement chunks into local vector store from {input_dir}...")
            chunk_files = list(input_dir.glob("*_chunks.json"))
            total_added = 0
            for chunk_file in sorted(chunk_files):
                added = rag_pipeline.index_processed_chunks_file(chunk_file)
                total_added += added
                print(f"  * Indexed {added} chunks from {chunk_file.name}")

            print(f"\n[COMPLETED] Successfully indexed {total_added} vector chunks into local vector store.")

        if args.query:
            print(f"\nExecuting local semantic search query: '{args.query}'...")
            response = rag_pipeline.query(args.query, company_filter=args.company, top_k=args.top_k)
            print(f"=======================================================")
            print(f"[LOCAL RAG QUERY RESPONSE] Latency: {response.retrieval_latency_ms:.2f}ms | Status: {response.status}")
            print(f"-------------------------------------------------------")
            for idx, match in enumerate(response.retrieved_chunks):
                print(f"Match #{idx+1} [Score: {match.similarity_score:.4f}] - {match.company_name} ({match.note_title}):")
                print(f"  {match.text[:200]}...\n")
            print(f"=======================================================")


if __name__ == "__main__":
    main()
