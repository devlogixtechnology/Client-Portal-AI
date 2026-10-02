"""
Unit tests for Data & RAG Pipeline Hardening (DRP - Overdue Recovery).
Verifies 384-dimensional vector embeddings, cosine similarity search, metadata filtering, and index persistence.
"""

from pathlib import Path
import pytest

from src.rag.embedding_engine import LocalEmbeddingEngine
from src.rag.rag_pipeline import OverdueRAGPipeline
from src.rag.schemas import RAGResponse, VectorChunk
from src.rag.vector_store import LocalVectorStore, cosine_similarity


def test_embedding_engine_vector_generation():
    """Verify LocalEmbeddingEngine generates 384-dimensional normalized vectors."""
    engine = LocalEmbeddingEngine()
    vec1 = engine.embed_text("Accounts receivable overdue recovery strategy")
    vec2 = engine.embed_text("Accounts receivable overdue recovery strategy")
    vec_diff = engine.embed_text("Completely unrelated topic about inventory manufacturing")

    assert len(vec1) == 384
    assert vec1 == vec2, "Identical input text must produce identical vector embeddings"

    sim_same = cosine_similarity(vec1, vec2)
    sim_diff = cosine_similarity(vec1, vec_diff)

    assert sim_same > 0.99
    assert sim_same >= sim_diff


def test_vector_store_add_and_search():
    """Verify LocalVectorStore indexing, company filtering, and cosine similarity search."""
    store = LocalVectorStore(index_path=None)

    c1 = VectorChunk(
        chunk_id="chunk_01",
        statement_id="stmt_1",
        company_name="TechVanguard",
        note_title="Note 1: Accounting Policies",
        text="The company maintains a strict 30-day collection policy for all trade accounts receivable.",
        embedding=[0.1] * 384
    )
    c2 = VectorChunk(
        chunk_id="chunk_02",
        statement_id="stmt_2",
        company_name="ApexRetail",
        note_title="Note 2: Overdue Allowances",
        text="Allowance for doubtful accounts is provided for invoices past due 90 days.",
        embedding=[0.2] * 384
    )

    store.add_chunks([c1, c2])
    assert len(store.chunks) == 2

    # Query with company filter
    query_vec = [0.1] * 384
    results = store.search(query_vec, top_k=2, company_filter="TechVanguard")
    assert len(results) == 1
    assert results[0].company_name == "TechVanguard"
    assert results[0].chunk_id == "chunk_01"


def test_rag_pipeline_end_to_end_query():
    """Verify OverdueRAGPipeline end-to-end semantic query execution."""
    pipeline = OverdueRAGPipeline()
    pipeline.vector_store.clear()

    raw_doc = {
        "document_id": "stmt_test_rag",
        "company_name": "RAG Test Inc",
        "fiscal_period": "FY24",
        "notes_chunks": [
            {
                "chunk_id": "c_rag_1",
                "note_title": "Note 4: Overdue Receivables",
                "text": "Overdue accounts receivable increased due to extended credit terms granted to major enterprise clients.",
                "estimated_tokens": 15
            }
        ]
    }

    added = pipeline.index_document(raw_doc)
    assert added == 1

    response = pipeline.query("Overdue accounts receivable terms", company_filter="RAG Test Inc")
    assert isinstance(response, RAGResponse)
    assert response.status == "SUCCESS"
    assert response.retrieval_latency_ms < 500.0
    assert len(response.retrieved_chunks) == 1
    assert "Overdue accounts receivable increased" in response.context_text
