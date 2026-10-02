"""
Data schemas for the Data & RAG Pipeline Hardening (DRP - Overdue Recovery).
Defines strongly-typed contracts for vector chunks, query embeddings, similarity search results, and RAG context payloads using Pydantic v2.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VectorChunk(BaseModel):
    """Represents a text chunk indexed in the local vector store with its embedding vector."""
    chunk_id: str = Field(..., description="Unique chunk identifier")
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
    statement_id: str = Field(..., description="Parent statement ID")
    company_name: str = Field(..., description="Company name")
    note_title: str = Field(..., description="Section title")
    text: str = Field(..., description="Retrieved chunk text content")
    similarity_score: float = Field(..., ge=-1.0, le=1.0, description="Cosine similarity score (0.0 to 1.0)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")


class RAGQueryRequest(BaseModel):
    """Query request payload for the RAG retriever."""
    query: str = Field(..., description="Semantic search query text")
    company_filter: Optional[str] = Field(None, description="Optional company name filter")
    top_k: int = Field(3, ge=1, le=10, description="Number of top matching chunks to retrieve")


class RAGResponse(BaseModel):
    """Structured RAG response container output by the retriever."""
    query: str = Field(..., description="Input query text")
    retrieved_chunks: List[QueryResult] = Field(default_factory=list, description="List of top-k retrieved matching chunks")
    context_text: str = Field("", description="Concatenated top-k context ready for LLM consumption")
    retrieval_latency_ms: float = Field(..., description="Retrieval latency in milliseconds")
    status: str = Field("SUCCESS", description="Retrieval execution status")
