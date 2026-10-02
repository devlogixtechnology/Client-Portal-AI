"""
Local Offline ChromaDB Vector Store (DRP-2: ChromaDB + MiniLM) for LedgerLense.
Provides persistent vector storage under data/processed/chroma_db using local MiniLM embeddings
with deterministic fallback for socket-isolated testing and environments without native C++ bindings.
"""

from pathlib import Path
import json
import logging
import time
from typing import Any, Dict, List, Optional

from src.rag.embedding_engine import LocalEmbeddingEngine
from src.rag.schemas import (
    ChromaCollectionConfig,
    ChromaQueryResult,
    ChromaStoreResult,
    VectorChunk,
)
from src.rag.vector_store import LocalVectorStore, cosine_similarity

logger = logging.getLogger(__name__)


class ChromaOfflineVectorStore:
    """Offline ChromaDB vector store wrapper with persistent storage and MiniLM embeddings."""

    def __init__(
        self,
        config: Optional[ChromaCollectionConfig] = None,
        embedding_engine: Optional[LocalEmbeddingEngine] = None
    ):
        self.config = config or ChromaCollectionConfig()
        self.embedding_engine = embedding_engine or LocalEmbeddingEngine(model_dir=self.config.embedding_model_path)
        self.persist_dir = Path(self.config.persist_directory)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        self._chroma_client = None
        self._collection = None
        self._fallback_store = LocalVectorStore(index_path=self.persist_dir / "chroma_fallback_index.json")

        self._init_chroma_client()

    def _init_chroma_client(self):
        """Initializes persistent ChromaDB client if available."""
        try:
            import chromadb
            from chromadb.config import Settings

            self._chroma_client = chromadb.PersistentClient(
                path=str(self.persist_dir),
                settings=Settings(anonymized_telemetry=False, allow_reset=True)
            )

            # Get or create collection
            metadata = {"hnsw:space": "cosine"} if self.config.distance_metric == "cosine" else {}
            self._collection = self._chroma_client.get_or_create_collection(
                name=self.config.collection_name,
                metadata=metadata
            )
            logger.info(f"Initialized ChromaDB persistent collection '{self.config.collection_name}' at {self.persist_dir}")
        except Exception as e:
            logger.info(f"ChromaDB native initialization skipped or offline fallback mode active: {e}. Engaging local offline vector store fallback.")

    def add_chunks(self, chunks: List[VectorChunk]) -> ChromaStoreResult:
        """Upserts a list of VectorChunk objects into the ChromaDB collection."""
        start_time = time.perf_counter()

        if not chunks:
            return ChromaStoreResult(
                collection_name=self.config.collection_name,
                total_documents=self.get_count(),
                status="SUCCESS",
                latency_ms=0.0
            )

        # Deduplicate chunks by chunk_id to ensure unique IDs for ChromaDB
        unique_chunks = []
        seen_ids = set()
        for c in chunks:
            if c.chunk_id not in seen_ids:
                seen_ids.add(c.chunk_id)
                unique_chunks.append(c)
        chunks = unique_chunks

        # 1. Generate embeddings if missing
        ids = [c.chunk_id for c in chunks]
        texts = [c.text for c in chunks]
        embeddings = [c.embedding if c.embedding else self.embedding_engine.embed_text(c.text) for c in chunks]
        metadatas = [
            {
                "tenant_id": c.tenant_id,
                "statement_id": c.statement_id,
                "company_name": c.company_name,
                "fiscal_period": c.fiscal_period,
                "note_title": c.note_title,
                "estimated_tokens": c.estimated_tokens
            }
            for c in chunks
        ]

        status_str = "SUCCESS"

        if self._collection is not None:
            try:
                self._collection.upsert(
                    ids=ids,
                    documents=texts,
                    embeddings=embeddings,
                    metadatas=metadatas
                )
            except Exception as e:
                logger.warning(f"ChromaDB upsert fallback triggered: {e}")
                status_str = "FALLBACK"
                self._fallback_store.add_chunks(chunks)
                self._fallback_store.save_index()
        else:
            status_str = "FALLBACK"
            self._fallback_store.add_chunks(chunks)
            self._fallback_store.save_index()

        latency_ms = (time.perf_counter() - start_time) * 1000

        return ChromaStoreResult(
            collection_name=self.config.collection_name,
            total_documents=self.get_count(),
            status=status_str,
            latency_ms=round(latency_ms, 2)
        )

    def query_similar(
        self,
        query_text: str,
        company_filter: Optional[str] = None,
        tenant_id: Optional[str] = None,
        top_k: int = 3
    ) -> List[ChromaQueryResult]:
        """
        Queries top_k similar chunks from ChromaDB by cosine distance.
        Applies optional tenant_id and company_filter, returning formatted ChromaQueryResult matches.
        """
        query_vec = self.embedding_engine.embed_text(query_text)

        if self._collection is not None:
            try:
                where_clause = {}
                if tenant_id and tenant_id.strip():
                    where_clause["tenant_id"] = {"$eq": tenant_id.strip()}
                if company_filter and company_filter.strip():
                    where_clause["company_name"] = {"$eq": company_filter.strip()}

                res = self._collection.query(
                    query_embeddings=[query_vec],
                    n_results=top_k,
                    where=where_clause if where_clause else None,
                    include=["documents", "metadatas", "distances"]
                )

                query_results: List[ChromaQueryResult] = []
                if res and res.get("ids") and res["ids"][0]:
                    matched_ids = res["ids"][0]
                    matched_docs = res["documents"][0]
                    matched_metas = res["metadatas"][0]
                    matched_dists = res["distances"][0]

                    for idx in range(len(matched_ids)):
                        dist = float(matched_dists[idx])
                        sim = max(0.0, 1.0 - dist)
                        meta = matched_metas[idx]
                        query_results.append(
                            ChromaQueryResult(
                                chunk_id=matched_ids[idx],
                                tenant_id=meta.get("tenant_id", "default_tenant"),
                                statement_id=meta.get("statement_id", ""),
                                company_name=meta.get("company_name", ""),
                                note_title=meta.get("note_title", "Notes to Accounts"),
                                text=matched_docs[idx],
                                distance=round(dist, 4),
                                similarity_score=round(sim, 4),
                                metadata=meta
                            )
                        )
                    return query_results
            except Exception as e:
                logger.info(f"ChromaDB query fallback triggered: {e}")

        # Fallback query handling
        fb_results = self._fallback_store.search(query_vec, top_k=top_k, company_filter=company_filter, tenant_id=tenant_id)
        return [
            ChromaQueryResult(
                chunk_id=r.chunk_id,
                tenant_id=r.tenant_id,
                statement_id=r.statement_id,
                company_name=r.company_name,
                note_title=r.note_title,
                text=r.text,
                distance=round(1.0 - r.similarity_score, 4),
                similarity_score=r.similarity_score,
                metadata=r.metadata
            )
            for r in fb_results
        ]


    def get_count(self) -> int:
        """Returns total document count in collection."""
        if self._collection is not None:
            try:
                return self._collection.count()
            except Exception:
                pass
        return len(self._fallback_store.chunks)

    def clear(self):
        """Clears all collection items."""
        if self._collection is not None:
            try:
                self._collection.delete(where={})
            except Exception:
                pass
        self._fallback_store.clear()
