"""
Data models for the Client Portal AI Financial Statement Ingestion Pipeline.
Provides structured schemas for line items, notes chunks, metadata, and full documents.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StatementType(str, Enum):
    BALANCE_SHEET = "balance_sheet"
    INCOME_STATEMENT = "income_statement"
    CASH_FLOW = "cash_flow"
    NOTES = "notes"
    UNKNOWN = "unknown"


class NormalizedLineItem(BaseModel):
    """Represents a standardized financial line item from a balance sheet or income statement."""
    standard_key: str = Field(..., description="Canonical key from financial taxonomy (e.g. 'revenue')")
    canonical_label: str = Field(..., description="Standardized human-readable label")
    original_label: str = Field(..., description="Exact raw line item label from the source file")
    statement_type: StatementType = Field(..., description="Type of financial statement")
    amount: Optional[float] = Field(None, description="Parsed numerical amount")
    period: str = Field("FY", description="Reporting period / fiscal year (e.g. '2024')")
    currency: str = Field("USD", description="Reported currency ISO or symbol")
    unit_multiplier: int = Field(1, description="Unit multiplier (1=exact, 1000=thousands, 1000000=millions)")
    raw_amount_str: str = Field("", description="Raw string amount from source")
    confidence_score: float = Field(1.0, description="Normalization confidence score between 0.0 and 1.0")
    is_total: bool = Field(False, description="Whether this line represents a subtotal or total")
    source_location: Optional[str] = Field(None, description="Location in source document (e.g., Page 1 / Sheet1:Row10)")


class NotesChunk(BaseModel):
    """Represents a narrative section chunk (e.g. from Notes to Accounts) ready for vector embedding."""
    chunk_id: str = Field(..., description="Unique chunk identifier")
    statement_id: str = Field(..., description="ID of parent financial statement document")
    company_name: str = Field(..., description="Name of the reporting entity")
    fiscal_period: str = Field(..., description="Reporting fiscal period")
    note_number: Optional[str] = Field(None, description="Note identifier e.g. 'Note 1', '2'")
    note_title: str = Field(..., description="Title or header of the note section")
    chunk_index: int = Field(0, description="Zero-based index of this chunk within the note")
    total_chunks_in_note: int = Field(1, description="Total number of chunks in this note section")
    text: str = Field(..., description="Cleaned text content ready for embedding")
    character_count: int = Field(0, description="Character length of text")
    estimated_tokens: int = Field(0, description="Estimated token count (approx chars / 4)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Embedding-ready search and filter metadata")


class FinancialStatementMetadata(BaseModel):
    """Metadata for an ingested financial statement document."""
    company_name: str = Field(..., description="Reporting company name")
    document_title: str = Field(..., description="Title of financial document")
    fiscal_period: str = Field(..., description="Fiscal period or year")
    currency: str = Field("USD", description="Reporting currency")
    unit: str = Field("exact", description="Unit specification: 'exact', 'thousands', 'millions'")
    source_file: str = Field(..., description="Filename or path of original document")
    file_type: str = Field(..., description="File type: 'pdf' or 'xlsx'")
    ingestion_timestamp: str = Field(..., description="ISO timestamp of ingestion")


class FinancialStatementDocument(BaseModel):
    """Top-level data structure produced by the ingestion pipeline."""
    document_id: str = Field(..., description="Unique ID for the financial statement")
    metadata: FinancialStatementMetadata = Field(..., description="Document level metadata")
    line_items: List[NormalizedLineItem] = Field(default_factory=list, description="List of extracted normalized line items")
    notes_chunks: List[NotesChunk] = Field(default_factory=list, description="List of chunked narrative text sections")
    summary_metrics: Dict[str, Optional[float]] = Field(
        default_factory=dict,
        description="Quick lookup map of key metrics (revenue, gross_profit, net_income, total_assets, etc.)"
    )
    raw_tables_count: int = Field(0, description="Count of tables parsed")
    notes_sections_count: int = Field(0, description="Count of distinct notes-to-accounts sections detected")


class ExtractedRawData(BaseModel):
    """Intermediate container for raw extracted text and tabular data before normalization and chunking."""
    company_name: Optional[str] = None
    fiscal_period: Optional[str] = None
    currency: str = "USD"
    unit_multiplier: int = 1
    tables: List[List[List[Any]]] = Field(default_factory=list, description="List of extracted tables (rows x cols)")
    narrative_sections: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of detected narrative sections e.g. [{'title': ..., 'text': ...}]"
    )
    raw_text: str = Field("", description="Full raw textual content")
    source_file: str = ""
    file_type: str = ""
    is_ocr_fallback_used: bool = Field(False, description="Whether Tesseract OCR fallback was used for scanned/low-density pages")
