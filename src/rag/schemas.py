"""
Data schemas for the Data & RAG Pipeline Hardening (DRP - Overdue Recovery, ChromaDB Setup & Multi-Tenant Data Isolation).
Defines strongly-typed contracts for vector chunks, query embeddings, similarity search results,
ChromaDB collection configs, TenantContext, MultiTenantQueryRequest, and MultiTenantQueryResponse using Pydantic v2.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TenantAccessViolationError(Exception):
    """Custom exception raised when multi-tenant data isolation rules or context boundaries are violated."""
    pass


class TenantContext(BaseModel):
    """Multi-tenant security context model for authorizing RAG queries."""
    tenant_id: str = Field(..., description="Unique client tenant identifier (e.g. 'tenant_techvanguard')")
    client_name: str = Field(..., description="Reporting company or client entity name")
    user_role: str = Field("analyst", description="Role of the requesting user (e.g. 'analyst', 'rm', 'client_admin')")
    permissions: List[str] = Field(default_factory=lambda: ["read_rag_chunks"], description="Authorized permission claims")


class VectorChunk(BaseModel):
    """Represents a text chunk indexed in the local vector store with its embedding vector and tenant scope."""
    chunk_id: str = Field(..., description="Unique chunk identifier")
    tenant_id: str = Field("default_tenant", description="Mandatory client tenant identifier for multi-tenant isolation")
    statement_id: str = Field(..., description="ID of parent financial statement document")
    company_name: str = Field(..., description="Name of reporting company")
    fiscal_period: str = Field("FY24", description="Reporting fiscal period")
    note_title: str = Field("Notes to Accounts", description="Section header or title")
    text: str = Field(..., description="Cleaned narrative chunk text")
    embedding: List[float] = Field(default_factory=list, description="384-dimensional normalized embedding vector")
    estimated_tokens: int = Field(0, description="Estimated token count")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata key-value pairs for filtering")


class QueryResult(BaseModel):
    """Represents a matched chunk result from vector similarity search."""
    chunk_id: str = Field(..., description="Matched chunk ID")
    tenant_id: str = Field("default_tenant", description="Tenant ID of matched chunk")
    statement_id: str = Field(..., description="Parent statement ID")
    company_name: str = Field(..., description="Company name")
    note_title: str = Field(..., description="Section title")
    text: str = Field(..., description="Retrieved chunk text content")
    similarity_score: float = Field(..., ge=-1.0, le=1.0, description="Cosine similarity score (0.0 to 1.0)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")


class ChromaCollectionConfig(BaseModel):
    """Configuration contract for local offline ChromaDB vector store."""
    collection_name: str = Field("ledgerlense_notes_chunks", description="ChromaDB collection identifier")
    persist_directory: str = Field("data/processed/chroma_db", description="Local disk persistence directory")
    distance_metric: str = Field("cosine", description="Distance metric: cosine, l2, or ip")
    embedding_model_path: str = Field("./models/all-MiniLM-L6-v2", description="Local pre-cached MiniLM model directory")


class ChromaQueryResult(BaseModel):
    """Result structure returned from ChromaDB similarity search queries."""
    chunk_id: str = Field(..., description="Matched chunk ID")
    tenant_id: str = Field("default_tenant", description="Tenant ID of matched chunk")
    statement_id: str = Field(..., description="Parent statement ID")
    company_name: str = Field(..., description="Reporting company name")
    note_title: str = Field(..., description="Section header title")
    text: str = Field(..., description="Matched chunk text content")
    distance: float = Field(..., description="Raw vector distance returned by ChromaDB")
    similarity_score: float = Field(..., description="Normalized similarity score (0.0 to 1.0)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary")


class ChromaStoreResult(BaseModel):
    """Summary result contract for ChromaDB vector operations."""
    collection_name: str = Field(..., description="Target ChromaDB collection name")
    total_documents: int = Field(0, description="Total count of documents in collection")
    status: str = Field("SUCCESS", description="Operation status ('SUCCESS', 'FALLBACK')")
    latency_ms: float = Field(..., description="Operation latency in milliseconds")


class RAGQueryRequest(BaseModel):
    """Query request payload for the RAG retriever."""
    query: str = Field(..., description="Semantic search query text")
    company_filter: Optional[str] = Field(None, description="Optional company name filter")
    tenant_id: Optional[str] = Field(None, description="Optional tenant identifier")
    top_k: int = Field(3, ge=1, le=10, description="Number of top matching chunks to retrieve")


class MultiTenantQueryRequest(BaseModel):
    """Strict multi-tenant query request payload mandating TenantContext authorization."""
    query: str = Field(..., description="Semantic search query text")
    tenant_context: TenantContext = Field(..., description="Mandatory tenant security context")
    top_k: int = Field(3, ge=1, le=10, description="Number of top matching chunks to retrieve")


class RAGResponse(BaseModel):
    """Structured RAG response container output by the retriever."""
    query: str = Field(..., description="Input query text")
    retrieved_chunks: List[QueryResult] = Field(default_factory=list, description="List of top-k retrieved matching chunks")
    context_text: str = Field("", description="Concatenated top-k context ready for LLM consumption")
    retrieval_latency_ms: float = Field(..., description="Retrieval latency in milliseconds")
    status: str = Field("SUCCESS", description="Retrieval execution status")


class MultiTenantQueryResponse(BaseModel):
    """Response container for tenant-isolated RAG queries including security verification assertions."""
    query: str = Field(..., description="Input query text")
    tenant_id: str = Field(..., description="Authorized tenant ID scope for this query")
    retrieved_chunks: List[QueryResult] = Field(default_factory=list, description="List of tenant-isolated matched chunks")
    context_text: str = Field("", description="Concatenated top-k tenant-isolated context string")
    cross_tenant_leakage_detected: bool = Field(False, description="Security assertion flag: True if cross-tenant leakage occurred")
    retrieval_latency_ms: float = Field(..., description="Retrieval latency in milliseconds")
    status: str = Field("SUCCESS", description="Retrieval execution status")
