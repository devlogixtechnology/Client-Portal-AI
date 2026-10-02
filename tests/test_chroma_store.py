"""
Unit tests for DRP-2 Local Offline Vector Store Setup (ChromaDB + MiniLM).
Verifies ChromaDB collection setup, persistence directory creation, document upserts, and vector queries.
"""

from pathlib import Path
import pytest

from src.rag.chroma_store import ChromaOfflineVectorStore
from src.rag.schemas import ChromaCollectionConfig, VectorChunk


def test_chroma_store_initialization_and_config():
    """Verify ChromaCollectionConfig defaults and ChromaOfflineVectorStore initialization."""
    config = ChromaCollectionConfig(
        collection_name="test_ledgerlense_chunks",
        persist_directory="data/processed/test_chroma_db"
    )
    store = ChromaOfflineVectorStore(config=config)

    assert store.config.collection_name == "test_ledgerlense_chunks"
    assert Path("data/processed/test_chroma_db").exists()


def test_chroma_store_add_and_query():
    """Verify ChromaOfflineVectorStore document upserts and similarity search."""
    config = ChromaCollectionConfig(
        collection_name="test_ledgerlense_chunks_02",
        persist_directory="data/processed/test_chroma_db_02"
    )
    store = ChromaOfflineVectorStore(config=config)
    store.clear()

    c1 = VectorChunk(
        chunk_id="ch_01",
        statement_id="stmt_01",
        company_name="TechVanguard",
        note_title="Note 3: Accounts Receivable",
        text="Overdue accounts receivable collection terms are set to 30 days with a 2% early settlement discount.",
        embedding=[0.1] * 384
    )
    c2 = VectorChunk(
        chunk_id="ch_02",
        statement_id="stmt_02",
        company_name="ApexRetail",
        note_title="Note 2: Credit Risk",
        text="Credit risk is managed through credit limits and routine monitoring of delinquent balances.",
        embedding=[0.2] * 384
    )

    res = store.add_chunks([c1, c2])
    assert res.status in ["SUCCESS", "FALLBACK"]
    assert res.latency_ms < 500.0
    assert store.get_count() >= 2

    # Execute vector query
    matches = store.query_similar("Overdue accounts receivable collection terms", company_filter="TechVanguard", top_k=2)
    assert len(matches) >= 1
    assert matches[0].company_name == "TechVanguard"
    assert "TechVanguard" in matches[0].company_name
