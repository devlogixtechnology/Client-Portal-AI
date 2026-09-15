"""Tests for NotesChunker section-aware splitting and metadata retention."""
import pytest
from src.chunking.notes_chunker import NotesChunker

SAMPLE_NOTES_TEXT = """
Note 1 - Summary of Significant Accounting Policies
The company prepares statements in accordance with IFRS. Revenue is recognized at point of delivery.
Inventories are stated at the lower of cost and net realizable value using FIFO.

Note 2 - Long-Term Debt and Borrowings
The company has a $20M credit line bearing interest at SOFR + 2.0%.
All debt covenants were met throughout the reporting period.

Note 3: Contingencies and Commitments
The company has non-cancelable lease obligations of $5M expiring in 2028.
No litigation claims are pending.
"""

def test_notes_chunker_section_detection():
    chunker = NotesChunker(target_chunk_size=500, chunk_overlap=50)
    sections = chunker._split_into_sections(SAMPLE_NOTES_TEXT)
    assert len(sections) == 3
    assert sections[0]["note_number"] == "1"
    assert "Accounting Policies" in sections[0]["note_title"]
    assert sections[1]["note_number"] == "2"
    assert sections[2]["note_number"] == "3"

def test_notes_chunker_end_to_end():
    chunker = NotesChunker(target_chunk_size=400, chunk_overlap=50)
    chunks = chunker.chunk_notes(
        raw_sections=[{"text": SAMPLE_NOTES_TEXT}],
        full_text="",
        company_name="TestCorp",
        fiscal_period="FY2024",
        statement_id="stmt_test",
        source_file="test.pdf"
    )

    assert len(chunks) >= 3
    for chunk in chunks:
        assert chunk.company_name == "TestCorp"
        assert chunk.fiscal_period == "FY2024"
        assert chunk.statement_id == "stmt_test"
        assert chunk.text.startswith("[TestCorp | FY2024 | Note")
        assert chunk.estimated_tokens > 0
        assert chunk.metadata["type"] == "notes_to_accounts"
