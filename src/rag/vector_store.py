"""
Local Offline Vector Store (DRP - Overdue Recovery) for LedgerLense.
Provides in-memory vector index, cosine similarity search, top-k ranking,
metadata filtering, and persistent JSON index storage under data/processed/vector_index.json.
"""

import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.rag.schemas import QueryResult, VectorChunk

logger = logging.getLogger(__name__)


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Computes cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_v1 = math.sqrt(sum(a * a for a in v1))
    norm_v2 = math.sqrt(sum(b * b for b in v2))
    if norm_v1 == 0.0 or norm_v2 == 0.0:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)


class LocalVectorStore:
    """In-memory vector store supporting cosine similarity and index persistence."""

    def __init__(self, index_path: Optional[str | Path] = "data/processed/vector_index.json"):
        self.chunks: List[VectorChunk] = []
        self.index_path = Path(index_path) if index_path else None
        self._load_index_if_exists()

    def _load_index_if_exists(self):
        """Loads index file if present on disk."""
        if self.index_path and self.index_path.exists():
            try:
                with open(self.index_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.chunks = [VectorChunk(**item) for item in data]
                logger.info(f"Loaded {len(self.chunks)} vector chunks from {self.index_path}")
            except Exception as e:
                logger.warning(f"Could not load vector index from {self.index_path}: {e}")

    def add_chunks(self, chunks: List[VectorChunk]) -> int:
        """Adds a list of VectorChunk objects to the index."""
        added = 0
        existing_ids = {c.chunk_id for c in self.chunks}
        for chunk in chunks:
            if chunk.chunk_id not in existing_ids:
                self.chunks.append(chunk)
                existing_ids.add(chunk.chunk_id)
                added += 1
        return added

    def search(
        self,
        query_vector: List[float],
        top_k: int = 3,
        company_filter: Optional[str] = None
    ) -> List[QueryResult]:
        """
        Executes cosine similarity search against indexed vector chunks.
        Applies optional company_filter and returns top_k QueryResult matches.
        """
        if not self.chunks or not query_vector:
            return []

        candidates = self.chunks
        if company_filter and company_filter.strip():
            filter_lower = company_filter.lower().strip()
            candidates = [c for c in candidates if filter_lower in c.company_name.lower()]

        scored_results: List[QueryResult] = []
        for chunk in candidates:
            score = cosine_similarity(query_vector, chunk.embedding)
            scored_results.append(
                QueryResult(
                    chunk_id=chunk.chunk_id,
                    statement_id=chunk.statement_id,
                    company_name=chunk.company_name,
                    note_title=chunk.note_title,
                    text=chunk.text,
                    similarity_score=round(score, 4),
                    metadata=chunk.metadata
                )
            )

        # Sort descending by similarity score
        scored_results.sort(key=lambda x: x.similarity_score, reverse=True)
        return scored_results[:top_k]

    def save_index(self, out_path: Optional[str | Path] = None) -> Path:
        """Saves current vector index to JSON file."""
        target_path = Path(out_path) if out_path else (self.index_path or Path("data/processed/vector_index.json"))
        target_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [c.model_dump() for c in self.chunks]
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(self.chunks)} vector chunks to {target_path}")
        return target_path

    def clear(self):
        """Clears all indexed chunks."""
        self.chunks.clear()
