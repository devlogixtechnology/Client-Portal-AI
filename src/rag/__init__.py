"""
Data & RAG Pipeline Hardening (DRP - Overdue Recovery, ChromaDB Setup & Multi-Tenant Data Isolation) Package.
"""

from src.rag.chroma_store import ChromaOfflineVectorStore
from src.rag.embedding_engine import LocalEmbeddingEngine
from src.rag.rag_pipeline import OverdueRAGPipeline
from src.rag.schemas import (
    ChromaCollectionConfig,
    ChromaQueryResult,
    ChromaStoreResult,
    MultiTenantQueryRequest,
    MultiTenantQueryResponse,
    QueryResult,
    RAGQueryRequest,
    RAGResponse,
    TenantAccessViolationError,
    TenantContext,
    VectorChunk,
)
from src.rag.vector_store import LocalVectorStore

__all__ = [
    "OverdueRAGPipeline",
    "LocalVectorStore",
    "ChromaOfflineVectorStore",
    "LocalEmbeddingEngine",
    "VectorChunk",
    "QueryResult",
    "ChromaCollectionConfig",
    "ChromaQueryResult",
    "ChromaStoreResult",
    "TenantContext",
    "MultiTenantQueryRequest",
    "MultiTenantQueryResponse",
    "TenantAccessViolationError",
    "RAGQueryRequest",
    "RAGResponse",
]
