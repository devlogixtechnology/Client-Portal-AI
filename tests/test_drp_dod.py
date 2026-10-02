"""
Definition of Done (DoD) & Acceptance Criteria Verification for DRP:
1. Core RAG & Vector Store pipeline fully implemented with zero syntax errors or unhandled exceptions.
2. Automated unit test script passes 100% locally.
3. Execution verified under physical offline network conditions (zero outbound cloud API calls).
4. Semantic query retrieval latency strictly < 500ms.
5. All 5 sample financial statements indexed and searchable via semantic RAG retriever.
"""

import json
from pathlib import Path
from unittest.mock import patch
import pytest

from src.pipeline import FinancialIngestionPipeline
from src.rag.rag_pipeline import OverdueRAGPipeline

SAMPLES = [
    "Sample_1_TechVanguard_FY24.pdf",
    "Sample_2_ApexRetail_FY24.xlsx",
    "Sample_3_BioHealth_Diagnostics_FY24.pdf",
    "Sample_4_PrecisionManufacturing_FY24.xlsx",
    "Sample_5_CleanEnergySolutions_FY24.pdf",
]


def blocked_socket(*args, **kwargs):
    raise RuntimeError("ILLEGAL EXTERNAL NETWORK ACCESS ATTEMPTED IN DRP RAG PIPELINE!")


def test_drp_dod_all_five_samples_offline():
    """Verify DRP RAG pipeline indexes all 5 sample statements 100% offline within 500ms retrieval budget."""
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    ingestion = FinancialIngestionPipeline()
    rag_pipeline = OverdueRAGPipeline()
    rag_pipeline.vector_store.clear()

    with patch("socket.socket.connect", side_effect=blocked_socket), \
         patch("socket.create_connection", side_effect=blocked_socket):

        # 1. Ingest & Index all 5 sample financial statements
        for sample_name in SAMPLES:
            file_path = raw_dir / sample_name
            assert file_path.exists(), f"Sample missing: {file_path}"

            doc = ingestion.ingest_file(file_path, output_dir=processed_dir)
            added = rag_pipeline.index_document(doc)
            assert added > 0, f"Must index note chunks for {sample_name}"

        # 2. Execute semantic RAG queries and verify latency < 500ms
        queries = [
            "What is the collection policy and overdue receivables allowance?",
            "Notes to Accounts disclosures regarding debt covenants and liquidity",
            "Contingent liabilities and legal litigation risks"
        ]

        for query_text in queries:
            response = rag_pipeline.query(query_text, top_k=3)
            assert response is not None
            assert response.status == "SUCCESS"
            assert response.retrieval_latency_ms < 500.0, f"Retrieval latency {response.retrieval_latency_ms}ms exceeds 500ms budget"
            assert len(response.retrieved_chunks) > 0
            assert len(response.context_text) > 50

        # 3. Verify Vector Store Index File Persistence
        index_file = processed_dir / "vector_index.json"
        assert index_file.exists(), "Vector store index file must exist on disk"
        with open(index_file, "r", encoding="utf-8") as f:
            indexed_data = json.load(f)
            assert len(indexed_data) >= 5, "Must contain at least 5 indexed vector chunks"
            for chunk in indexed_data:
                assert "embedding" in chunk
                assert len(chunk["embedding"]) == 384
                assert "text" in chunk
                assert "company_name" in chunk
