"""
Definition of Done (DoD) automated sanity test suite for DRP-3: Client Multi-Tenant Data Isolation at RAG Layer.
Validates socket-level offline isolation, zero cross-tenant data leakage, sub-500ms latency,
and strict multi-tenant authorization.
"""

import socket
import time
from pathlib import Path
import pytest

from src.rag.schemas import (
    TenantContext,
    MultiTenantQueryRequest,
    MultiTenantQueryResponse,
    TenantAccessViolationError,
)
from src.rag.rag_pipeline import OverdueRAGPipeline
from src.rag.vector_store import LocalVectorStore
from src.rag.chroma_store import ChromaOfflineVectorStore


@pytest.fixture(autouse=True)
def block_network():
    """Guard fixture enforcing 100% offline network isolation by blocking outbound socket connections."""
    original_socket = socket.socket

    def guard_socket(*args, **kwargs):
        raise RuntimeError("NETWORK ATTEMPT DETECTED: DRP-3 must run 100% offline without network socket calls!")

    socket.socket = guard_socket
    yield
    socket.socket = original_socket


def test_drp3_multi_tenant_isolation_dod(tmp_path):
    """
    DoD Test: Multi-Tenant Data Isolation at RAG Layer.
    - Index 5 distinct sample financial statements under unique tenant IDs.
    - Query RAG pipeline for each tenant.
    - Assert zero cross-tenant data leakage (cross_tenant_leakage_detected == False).
    - Assert retrieval latency < 500ms.
    """
    data_dir = Path("data/processed")
    sample_files = list(data_dir.glob("stmt_sample_*_chunks.json"))
    assert len(sample_files) >= 5, f"Expected at least 5 sample chunk files in data/processed, found {len(sample_files)}"

    store_file = tmp_path / "dod_drp3_vector_store.json"
    vec_store = LocalVectorStore(index_path=store_file)
    pipeline = OverdueRAGPipeline(vector_store=vec_store)

    tenant_map = {}
    for idx, sample_file in enumerate(sample_files[:5], start=1):
        tenant_id = f"tenant_sample_{idx}"
        added = pipeline.index_processed_chunks_file(sample_file, tenant_id=tenant_id)
        assert added > 0, f"Failed to index chunks from {sample_file.name} for tenant {tenant_id}"
        tenant_map[tenant_id] = sample_file.name

    # Perform tenant-isolated queries for each tenant
    query_terms = [
        "overdue trade receivables balance",
        "doubtful debts provision allowance",
        "credit risk exposure and concentration",
        "aging analysis 90 days past due",
        "repayment terms and liquidity management"
    ]

    for tenant_id, source_file in tenant_map.items():
        ctx = TenantContext(
            tenant_id=tenant_id,
            client_name=f"Client {tenant_id.title()}",
            user_role="analyst"
        )

        for query_text in query_terms:
            t0 = time.perf_counter()
            response = pipeline.query_tenant_isolated(query_text=query_text, tenant_context=ctx, top_k=3)
            elapsed_ms = (time.perf_counter() - t0) * 1000

            # Assertions
            assert response.status == "SUCCESS"
            assert response.tenant_id == tenant_id
            assert response.cross_tenant_leakage_detected is False, f"Cross-tenant data leakage detected for tenant {tenant_id}!"
            assert elapsed_ms < 500.0, f"Latency limit exceeded: {elapsed_ms:.2f}ms > 500ms target"

            # Check that every retrieved chunk strictly belongs to the queried tenant_id
            for chunk in response.retrieved_chunks:
                assert chunk.tenant_id == tenant_id, f"Data leakage error! Found chunk from tenant {chunk.tenant_id} during query for {tenant_id}"


def test_drp3_tenant_access_violation_guard():
    """DoD Test: Verify security guard blocks unauthorized or context-less tenant queries."""
    pipeline = OverdueRAGPipeline()

    # Unauthenticated / empty tenant context
    with pytest.raises(TenantAccessViolationError):
        pipeline.query_tenant_isolated("receivables summary", tenant_context=None)

    empty_ctx = TenantContext(tenant_id="", client_name="Unknown Entity")
    with pytest.raises(TenantAccessViolationError):
        pipeline.query_tenant_isolated("receivables summary", tenant_context=empty_ctx)
