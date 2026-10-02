"""
Overdue Receivables RAG Pipeline (DRP - Overdue Recovery) for LedgerLense.
Orchestrates semantic vector indexing of financial statement Notes to Accounts chunks
and executes context retrieval for overdue recovery, debt collection disclosures, and credit risk queries.
"""

from pathlib import Path
import json
import logging
import time
from typing import Any, Dict, List, Optional

from src.models import FinancialStatementDocument
from src.rag.embedding_engine import LocalEmbeddingEngine
from src.rag.schemas import QueryResult, RAGQueryRequest, RAGResponse, VectorChunk
from src.rag.vector_store import LocalVectorStore

logger = logging.getLogger(__name__)


class OverdueRAGPipeline:
    """Master RAG Pipeline for indexing financial chunks and semantic context retrieval."""

    def __init__(
        self,
        embedding_engine: Optional[LocalEmbeddingEngine] = None,
        vector_store: Optional[LocalVectorStore] = None
    ):
        self.embedding_engine = embedding_engine or LocalEmbeddingEngine()
        self.vector_store = vector_store or LocalVectorStore()

    def index_document(self, document: FinancialStatementDocument | Dict[str, Any]) -> int:
        """Indexes all narrative notes chunks from a financial statement document."""
        if isinstance(document, FinancialStatementDocument):
            doc_id = document.document_id
            company_name = document.metadata.company_name
            fiscal_period = document.metadata.fiscal_period
            chunks = document.notes_chunks
        else:
            doc_id = document.get("document_id", "stmt_unknown")
            meta = document.get("metadata", {})
            company_name = meta.get("company_name", document.get("company_name", "Unknown Corp"))
            fiscal_period = meta.get("fiscal_period", document.get("fiscal_period", "FY24"))
            chunks = document.get("notes_chunks", [])

        vector_chunks: List[VectorChunk] = []

        for idx, c in enumerate(chunks):
            if isinstance(c, dict):
                chunk_id = c.get("chunk_id", f"{doc_id}_c{idx}")
                text = c.get("text", "")
                note_title = c.get("note_title", "Notes to Accounts")
                meta = c.get("metadata", {})
                est_tokens = c.get("estimated_tokens", len(text) // 4)
            else:
                chunk_id = getattr(c, "chunk_id", f"{doc_id}_c{idx}")
                text = getattr(c, "text", "")
                note_title = getattr(c, "note_title", "Notes to Accounts")
                meta = getattr(c, "metadata", {})
                est_tokens = getattr(c, "estimated_tokens", len(text) // 4)

            if text:
                embedding = self.embedding_engine.embed_text(text)
                vector_chunks.append(
                    VectorChunk(
                        chunk_id=chunk_id,
                        statement_id=doc_id,
                        company_name=company_name,
                        fiscal_period=fiscal_period,
                        note_title=note_title,
                        text=text,
                        embedding=embedding,
                        estimated_tokens=est_tokens,
                        metadata=meta
                    )
                )

        added_count = self.vector_store.add_chunks(vector_chunks)
        if added_count > 0:
            self.vector_store.save_index()
        return added_count

    def index_processed_chunks_file(self, chunks_json_file: Path | str) -> int:
        """Indexes chunks directly from a `<statement_id>_chunks.json` file."""
        path = Path(chunks_json_file)
        if not path.exists():
            return 0
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        stmt_id = path.stem.replace("_chunks", "")
        company_name = stmt_id.replace("stmt_sample_", "").replace("_", " ").title()

        vector_chunks = []
        for idx, item in enumerate(data):
            text = item.get("text", "")
            if text:
                embedding = self.embedding_engine.embed_text(text)
                vector_chunks.append(
                    VectorChunk(
                        chunk_id=item.get("chunk_id", f"{stmt_id}_c{idx}"),
                        statement_id=stmt_id,
                        company_name=company_name,
                        note_title=item.get("note_title", "Notes to Accounts"),
                        text=text,
                        embedding=embedding,
                        estimated_tokens=item.get("estimated_tokens", len(text) // 4),
                        metadata=item.get("metadata", {})
                    )
                )

        added = self.vector_store.add_chunks(vector_chunks)
        if added > 0:
            self.vector_store.save_index()
        return added

    def query(
        self,
        query_text: str,
        company_filter: Optional[str] = None,
        top_k: int = 3
    ) -> RAGResponse:
        """
        Executes semantic search for a query and synthesizes top-k context ready for LLM consumption.
        """
        start_time = time.perf_counter()

        query_vec = self.embedding_engine.embed_text(query_text)
        results = self.vector_store.search(
            query_vector=query_vec,
            top_k=top_k,
            company_filter=company_filter
        )

        # Synthesize context blocks
        context_blocks = []
        for r in results:
            context_blocks.append(
                f"[Source: {r.company_name} | {r.note_title} | Score: {r.similarity_score:.4f}]\n{r.text}"
            )

        context_text = "\n\n---\n\n".join(context_blocks)
        latency_ms = (time.perf_counter() - start_time) * 1000

        return RAGResponse(
            query=query_text,
            retrieved_chunks=results,
            context_text=context_text,
            retrieval_latency_ms=round(latency_ms, 2),
            status="SUCCESS"
        )
