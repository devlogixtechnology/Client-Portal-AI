"""
Local Offline Embedding Engine (DRP - Overdue Recovery) for LedgerLense.
Generates 384-dimensional L2-normalized embedding vectors using pre-cached model weights
under ./models/all-MiniLM-L6-v2 with deterministic offline fallback for socket isolation testing.
"""

import hashlib
import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 384


class LocalEmbeddingEngine:
    """Offline embedding engine using local model weights or deterministic fallback."""

    def __init__(self, model_dir: str = "./models/all-MiniLM-L6-v2"):
        self.model_dir = Path(model_dir)
        self.dimension = EMBEDDING_DIM
        self._st_model = None
        self._load_local_weights()

    def _load_local_weights(self):
        """Attempts loading local sentence_transformers model if pre-cached."""
        if self.model_dir.exists():
            try:
                from sentence_transformers import SentenceTransformer
                self._st_model = SentenceTransformer(str(self.model_dir), device="cpu")
                logger.info(f"Loaded local sentence_transformer model from {self.model_dir}")
            except Exception as e:
                logger.info(f"SentenceTransformers local load skipped or offline mode active: {e}. Using deterministic local embedding fallback.")

    def embed_text(self, text: str) -> List[float]:
        """Generates 384-dimensional L2-normalized vector embedding for input text."""
        if not text or not text.strip():
            return [0.0] * self.dimension

        if self._st_model is not None:
            try:
                vec = self._st_model.encode(text, normalize_embeddings=True)
                return [float(x) for x in vec]
            except Exception as e:
                logger.warning(f"Embedding encoding fallback triggered: {e}")

        # Deterministic offline vector generation (L2-normalized 384-dim floats)
        return self._generate_deterministic_embedding(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a batch of text strings."""
        return [self.embed_text(t) for t in texts]

    def _generate_deterministic_embedding(self, text: str) -> List[float]:
        """Generates L2-normalized 384-dimensional vector deterministically from text content."""
        words = text.lower().split()
        vector = [0.0] * self.dimension

        for idx, word in enumerate(words):
            # Generate deterministic hash offset
            hash_bytes = hashlib.sha256(f"{word}_{idx % 7}".encode("utf-8")).digest()
            dim_idx = int.from_bytes(hash_bytes[:2], byteorder="big") % self.dimension
            weight = (int.from_bytes(hash_bytes[2:4], byteorder="big") / 65535.0) * 2.0 - 1.0
            vector[dim_idx] += weight

        # L2-normalization
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 1e-9:
            vector = [round(x / norm, 6) for x in vector]
        else:
            vector = [1.0 / math.sqrt(self.dimension)] * self.dimension

        return vector
