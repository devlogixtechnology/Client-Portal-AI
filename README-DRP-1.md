# Client Portal AI

> **Squad**: RAG & Knowledge Systems  
> **Squad Priority**: 🔴 Delivery-Critical (Target Deadline: Sept 25)  
> **Sprint Goal (Sprint 1)**: Stand up a fully offline RAG foundation financial-statement ingestion and local-LLM insight generation for Client Portal AI.  
> **Sprint Goal (Sprint 2)**: Harden Client Portal AI to delivery quality for Sept 25.  
> **Hard Constraint**: 100% Offline-only, in-house low-resource models (quantized Llama-3.2 / Phi-3 via Ollama) — **NO calls to hosted APIs at runtime**.

---

## Subtask: DRP-1. Financial Statement Ingestion Pipeline

The **Financial Statement Ingestion Pipeline** ingests raw client Balance Sheets and Income Statements (in both PDF and XLSX formats), extracts structured tabular accounting data, normalizes heterogeneous accounting terminology into a canonical taxonomy, and semantically chunks narrative footnote sections (Notes to Accounts) for offline vector embedding and local LLM reasoning.

### Definition of Done (DoD)
- **5 sample financial statements** (3 PDF, 2 XLSX) parsed into:
  - **Structured JSON** (`<statement_id>_structured.json`): Document metadata, canonical line items, original labels, confidence scores, multi-period comparative numbers, and summary metrics.
  - **Chunked Text JSON** (`<statement_id>_chunks.json`): Context-preserved narrative chunks from Notes to Accounts with rich embedding metadata (note title, company, period, token estimation).
- **Automated Verification**:
  - Full test suite passing with 100% offline network isolation testing.

---

## Directory Structure

```
Client Portal AI/
├── config/
│   └── taxonomy.py                  # Standard financial taxonomy & aliases (IFRS, US GAAP, SME)
├── data/
│   ├── raw/                         # 5 diverse sample financial statements
│   │   ├── Sample_1_TechVanguard_FY24.pdf           (Tech SaaS: Balance Sheet, Income Stmt, Notes 1-4)
│   │   ├── Sample_2_ApexRetail_FY24.xlsx            (Retail Corp: Balance Sheet, Income Stmt, Notes 1-3)
│   │   ├── Sample_3_BioHealth_Diagnostics_FY24.pdf  (Healthcare / GBP: Balance Sheet, Income Stmt, Notes 1-3)
│   │   ├── Sample_4_PrecisionManufacturing_FY24.xlsx(Manufacturing / EUR: Balance Sheet, Income Stmt, Notes 1-3)
│   │   └── Sample_5_CleanEnergySolutions_FY24.pdf   (Renewable Energy: Balance Sheet, Income Stmt, Notes 1-3)
│   └── processed/                   # Output structured JSON and RAG-ready chunks
│       ├── stmt_sample_1_techvanguard_fy24_chunks.json
│       ├── stmt_sample_1_techvanguard_fy24_structured.json
│       ├── stmt_sample_2_apexretail_fy24_chunks.json
│       ├── stmt_sample_2_apexretail_fy24_structured.json
│       ├── stmt_sample_3_biohealth_diagnostics_fy24_chunks.json
│       ├── stmt_sample_3_biohealth_diagnostics_fy24_structured.json
│       ├── stmt_sample_4_precisionmanufacturing_fy24_chunks.json
│       ├── stmt_sample_4_precisionmanufacturing_fy24_structured.json
│       ├── stmt_sample_5_cleanenergysolutions_fy24_chunks.json
│       └── stmt_sample_5_cleanenergysolutions_fy24_structured.json
├── src/
│   ├── models.py                    # Pydantic data schemas
│   ├── extractors/
│   │   ├── base.py                  # Base extractor interface and number cleaner
│   │   ├── pdf_extractor.py         # pdfplumber table & narrative extraction
│   │   └── excel_extractor.py       # openpyxl multi-sheet extraction
│   ├── normalizer/
│   │   └── line_item_normalizer.py  # Regex & alias matching to canonical taxonomy
│   ├── chunking/
│   │   └── notes_chunker.py         # Semantic section-aware chunker for Notes to Accounts
│   └── pipeline.py                  # FinancialIngestionPipeline orchestrator
├── scripts/
│   ├── generate_sample_data.py      # Deterministic generator for the 5 sample statements
│   └── run_ingestion.py             # CLI runner for batch or single-file ingestion
├── tests/
│   ├── test_pdf_extractor.py        # PDF extractor tests
│   ├── test_excel_extractor.py      # Excel extractor tests
│   ├── test_normalizer.py           # Taxonomy alias resolution & number cleaning tests
│   ├── test_notes_chunker.py        # Chunker boundary & metadata tests
│   ├── test_pipeline_dod.py         # Definition of Done assertions for all 5 samples
│   └── test_offline_integrity.py    # Zero-network isolation test
└── requirements.txt
```

---

## Installation & Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Generate Sample Statements**:
   ```bash
   python scripts/generate_sample_data.py
   ```

3. **Run Batch Ingestion**:
   ```bash
   python scripts/run_ingestion.py --input-dir data/raw --output-dir data/processed
   ```

4. **Ingest a Single Document**:
   ```bash
   python scripts/run_ingestion.py --file data/raw/Sample_1_TechVanguard_FY24.pdf --output-dir data/processed
   ```

5. **Run the Test Suite**:
   ```bash
   python -m pytest -v tests/
   ```

---

## Offline Constraint & Security Verification

Per project requirements, this pipeline strictly runs **100% offline** with **zero external API calls**:
- `tests/test_offline_integrity.py` monkeypatches network socket creation to block any external requests during ingestion.
- The pipeline uses purely local rule-based extractors (`pdfplumber`, `openpyxl`), deterministic hash/regex line-item normalizers, and local sliding-window section chunkers.
