"""
Master Ingestion Pipeline Orchestrator for Client Portal AI.
Coordinates extraction, line-item normalization, and notes-to-accounts chunking.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from src.chunking.notes_chunker import NotesChunker
from src.extractors.excel_extractor import ExcelExtractor
from src.extractors.pdf_extractor import PDFExtractor
from src.models import (
    FinancialStatementDocument,
    FinancialStatementMetadata,
    NormalizedLineItem,
    NotesChunk,
)
from src.normalizer.line_item_normalizer import LineItemNormalizer


class FinancialIngestionPipeline:
    """End-to-end offline ingestion pipeline for PDF/XLSX financial statements."""

    def __init__(self, target_chunk_size: int = 750, chunk_overlap: int = 100):
        self.pdf_extractor = PDFExtractor()
        self.excel_extractor = ExcelExtractor()
        self.normalizer = LineItemNormalizer()
        self.chunker = NotesChunker(
            target_chunk_size=target_chunk_size,
            chunk_overlap=chunk_overlap
        )

    def ingest_file(
        self,
        file_path: Path | str,
        output_dir: Optional[Path | str] = None
    ) -> FinancialStatementDocument:
        """
        Ingests a single financial statement file (PDF or XLSX) and returns structured document.
        Optionally saves output JSON artifacts in output_dir.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            raw_data = self.pdf_extractor.extract(file_path)
        elif suffix in (".xlsx", ".xlsm", ".xls"):
            raw_data = self.excel_extractor.extract(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}. Only .pdf and .xlsx are supported.")

        # 1. Normalize line items across all extracted tables
        all_line_items: List[NormalizedLineItem] = []
        for tbl_idx, tbl in enumerate(raw_data.tables):
            items = self.normalizer.parse_table(
                table_rows=tbl,
                default_currency=raw_data.currency,
                default_period=raw_data.fiscal_period or "FY",
                unit_multiplier=raw_data.unit_multiplier,
                source_prefix=f"Table{tbl_idx+1}"
            )
            all_line_items.extend(items)

        # 2. Derive Document ID
        safe_stem = file_path.stem.lower().replace(" ", "_").replace("-", "_")
        doc_id = f"stmt_{safe_stem}"

        # 3. Chunk Notes to Accounts
        notes_chunks: List[NotesChunk] = self.chunker.chunk_notes(
            raw_sections=raw_data.narrative_sections,
            full_text=raw_data.raw_text,
            company_name=raw_data.company_name or file_path.stem,
            fiscal_period=raw_data.fiscal_period or "FY",
            statement_id=doc_id,
            source_file=file_path.name
        )

        # 4. Compute Summary Metrics (highest confidence latest figures)
        summary_metrics: Dict[str, Optional[float]] = {}
        for key in ["revenue", "gross_profit", "operating_income", "net_income",
                     "total_assets", "total_liabilities", "total_stockholders_equity",
                     "cash_and_cash_equivalents"]:
            matching = [item for item in all_line_items if item.standard_key == key]
            if matching:
                # Pick one with highest confidence and largest/most complete period
                best = max(matching, key=lambda x: (x.confidence_score, x.period))
                summary_metrics[key] = best.amount
            else:
                summary_metrics[key] = None

        # 5. Build Metadata
        meta = FinancialStatementMetadata(
            company_name=raw_data.company_name or file_path.stem,
            document_title=f"{raw_data.company_name or file_path.stem} Financial Statement",
            fiscal_period=raw_data.fiscal_period or "FY",
            currency=raw_data.currency,
            unit="thousands" if raw_data.unit_multiplier == 1000 else ("millions" if raw_data.unit_multiplier == 1000000 else "exact"),
            source_file=file_path.name,
            file_type=raw_data.file_type,
            ingestion_timestamp=datetime.now(timezone.utc).isoformat()
        )

        doc = FinancialStatementDocument(
            document_id=doc_id,
            metadata=meta,
            line_items=all_line_items,
            notes_chunks=notes_chunks,
            summary_metrics=summary_metrics,
            raw_tables_count=len(raw_data.tables),
            notes_sections_count=len(set(c.note_title for c in notes_chunks))
        )

        # 6. Save JSON Artifacts if output_dir specified
        if output_dir:
            out_path = Path(output_dir)
            out_path.mkdir(parents=True, exist_ok=True)

            # 6a. Full Structured JSON
            structured_file = out_path / f"{doc_id}_structured.json"
            with open(structured_file, "w", encoding="utf-8") as f:
                json.dump(doc.model_dump(), f, indent=2, ensure_ascii=False)

            # 6b. RAG Ready Text Chunks JSON
            chunks_file = out_path / f"{doc_id}_chunks.json"
            chunks_payload = [
                {
                    "chunk_id": c.chunk_id,
                    "text": c.text,
                    "note_title": c.note_title,
                    "note_number": c.note_number,
                    "metadata": c.metadata,
                    "estimated_tokens": c.estimated_tokens
                }
                for c in notes_chunks
            ]
            with open(chunks_file, "w", encoding="utf-8") as f:
                json.dump(chunks_payload, f, indent=2, ensure_ascii=False)

        return doc

    def ingest_batch(
        self,
        input_dir: Path | str,
        output_dir: Optional[Path | str] = None
    ) -> List[FinancialStatementDocument]:
        """Batch processes all supported files in a directory."""
        input_dir = Path(input_dir)
        documents = []
        for file_path in sorted(input_dir.iterdir()):
            if file_path.suffix.lower() in (".pdf", ".xlsx", ".xlsm"):
                doc = self.ingest_file(file_path, output_dir=output_dir)
                documents.append(doc)
        return documents
