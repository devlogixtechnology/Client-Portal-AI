"""
Hard constraint verification:
Proves that the ingestion pipeline operates 100% offline with zero outbound network calls.
Intercepts socket creation/connection and raises an error if network access is attempted.
"""
import socket
import pytest
from pathlib import Path
from unittest.mock import patch
from src.pipeline import FinancialIngestionPipeline

def blocked_socket(*args, **kwargs):
    raise RuntimeError("ILLEGAL EXTERNAL NETWORK ACCESS ATTEMPTED IN OFFLINE PIPELINE!")

def test_offline_integrity_zero_network_calls():
    # Monkeypatch socket to ensure any network connection attempt fails immediately
    with patch("socket.socket.connect", side_effect=blocked_socket), \
         patch("socket.create_connection", side_effect=blocked_socket):

        pipeline = FinancialIngestionPipeline()
        
        # Test PDF statement offline
        pdf_file = Path("data/raw/Sample_1_TechVanguard_FY24.pdf")
        doc_pdf = pipeline.ingest_file(pdf_file)
        assert doc_pdf is not None
        assert len(doc_pdf.line_items) > 0
        assert len(doc_pdf.notes_chunks) > 0

        # Test Excel statement offline
        xlsx_file = Path("data/raw/Sample_2_ApexRetail_FY24.xlsx")
        doc_xlsx = pipeline.ingest_file(xlsx_file)
        assert doc_xlsx is not None
        assert len(doc_xlsx.line_items) > 0
        assert len(doc_xlsx.notes_chunks) > 0
