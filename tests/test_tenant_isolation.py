"""
Unit tests for DRP-3. Client Multi-Tenant Data Isolation at RAG Layer.
Verifies strongly-typed Pydantic schemas, tenant-isolated indexing, query filtering,
cross-tenant leakage prevention, and exception handling.
"""

import pytest
import time
from src.rag.schemas import (
    ChromaCollectionConfig,
    TenantContext,
    MultiTenantQueryRequest,
    MultiTenantQueryResponse,
    TenantAccessViolationError,
    VectorChunk,
    QueryResult,
)
from src.rag.rag_pipeline import OverdueRAGPipeline
from src.rag.chroma_store import ChromaOfflineVectorStore
from src.rag.vector_store import LocalVectorStore


def test_tenant_context_and_schemas():
    """Verify TenantContext and multi-tenant query models enforce strict validation."""
    ctx = TenantContext(
        tenant_id="tenant_alpha",
        client_name="Alpha Corp",
        user_role="rm",
        permissions=["read_rag_chunks"]
    )
    assert ctx.tenant_id == "tenant_alpha"
    assert ctx.client_name == "Alpha Corp"

    req = MultiTenantQueryRequest(
        query="overdue receivables balances",
        tenant_context=ctx,
        top_k=3
    )
    assert req.tenant_context.tenant_id == "tenant_alpha"
    assert req.top_k == 3


def test_in_memory_tenant_isolation(tmp_path):
    """Test multi-tenant isolation using LocalVectorStore in memory."""
    store_file = tmp_path / "test_store.json"
    vec_store = LocalVectorStore(index_path=store_file)
    pipeline = OverdueRAGPipeline(vector_store=vec_store)

    # Index doc for tenant_alpha
    doc_alpha = {
        "document_id": "stmt_sample_1_fy24",
        "company_name": "Alpha Ltd",
        "fiscal_period": "FY24",
        "notes_chunks": [
            {
                "chunk_id": "alpha_c1",
                "text": "Alpha Ltd has overdue trade receivables of $1.5M aged over 90 days.",
                "note_title": "Trade Receivables",
            }
        ]
    }
    pipeline.index_document(doc_alpha, tenant_id="tenant_alpha")

    # Index doc for tenant_beta
    doc_beta = {
        "document_id": "stmt_sample_2_fy24",
        "company_name": "Beta Inc",
        "fiscal_period": "FY24",
        "notes_chunks": [
            {
                "chunk_id": "beta_c1",
                "text": "Beta Inc has trade receivables allowance of $500k.",
                "note_title": "Receivables Allowance",
            }
        ]
    }
    pipeline.index_document(doc_beta, tenant_id="tenant_beta")

    # Query as tenant_alpha
    ctx_alpha = TenantContext(tenant_id="tenant_alpha", client_name="Alpha Ltd")
    resp_alpha = pipeline.query_tenant_isolated("overdue trade receivables", tenant_context=ctx_alpha)

    assert resp_alpha.status == "SUCCESS"
    assert resp_alpha.tenant_id == "tenant_alpha"
    assert resp_alpha.cross_tenant_leakage_detected is False
    assert len(resp_alpha.retrieved_chunks) > 0
    for chunk in resp_alpha.retrieved_chunks:
        assert chunk.tenant_id == "tenant_alpha"
        assert "Alpha Ltd" in chunk.company_name or "alpha" in chunk.chunk_id

    # Query as tenant_beta
    ctx_beta = TenantContext(tenant_id="tenant_beta", client_name="Beta Inc")
    resp_beta = pipeline.query_tenant_isolated("overdue trade receivables", tenant_context=ctx_beta)

    assert resp_beta.status == "SUCCESS"
    assert resp_beta.tenant_id == "tenant_beta"
    assert resp_beta.cross_tenant_leakage_detected is False
    assert len(resp_beta.retrieved_chunks) > 0
    for chunk in resp_beta.retrieved_chunks:
        assert chunk.tenant_id == "tenant_beta"
        assert "Beta Inc" in chunk.company_name or "beta" in chunk.chunk_id


def test_invalid_tenant_context_raises_exception():
    """Verify missing or empty tenant_id raises TenantAccessViolationError."""
    pipeline = OverdueRAGPipeline()
    invalid_ctx = TenantContext(tenant_id="   ", client_name="Empty Tenant")

    with pytest.raises(TenantAccessViolationError):
        pipeline.query_tenant_isolated("test query", tenant_context=invalid_ctx)


def test_chroma_multi_tenant_isolation(tmp_path):
    """Test multi-tenant metadata filtering using ChromaOfflineVectorStore."""
    chroma_dir = tmp_path / "chroma_test_db"
    config = ChromaCollectionConfig(
        collection_name="test_multi_tenant",
        persist_directory=str(chroma_dir)
    )
    chroma_store = ChromaOfflineVectorStore(config=config)

    chunks_alpha = [
        VectorChunk(
            chunk_id="alpha_chroma_1",
            tenant_id="tenant_alpha",
            statement_id="stmt_alpha",
            company_name="Alpha Tech",
            note_title="Credit Risk",
            text="Alpha Tech credit exposure is monitored closely with strictly 30 day credit limits.",
            embedding=[0.05] * 384
        )
    ]

    chunks_beta = [
        VectorChunk(
            chunk_id="beta_chroma_1",
            tenant_id="tenant_beta",
            statement_id="stmt_beta",
            company_name="Beta Logistics",
            note_title="Credit Risk",
            text="Beta Logistics overdue receivables balance stands at 2.4 million USD.",
            embedding=[0.05] * 384
        )
    ]

    chroma_store.add_chunks(chunks_alpha)
    chroma_store.add_chunks(chunks_beta)

    # Query Chroma for tenant_alpha
    results_alpha = chroma_store.query_similar(
        query_text="credit exposure balance",
        top_k=5,
        tenant_id="tenant_alpha"
    )

    assert len(results_alpha) == 1
    assert results_alpha[0].tenant_id == "tenant_alpha"
    assert results_alpha[0].chunk_id == "alpha_chroma_1"

    # Query Chroma for tenant_beta
    results_beta = chroma_store.query_similar(
        query_text="credit exposure balance",
        top_k=5,
        tenant_id="tenant_beta"
    )

    assert len(results_beta) == 1
    assert results_beta[0].tenant_id == "tenant_beta"
    assert results_beta[0].chunk_id == "beta_chroma_1"
