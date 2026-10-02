# Data & RAG Pipeline Hardening (DRP - Overdue Recovery)

> **Product**: LedgerLense  
> **Sprint**: Sprint 1  
> **Deliverable**: Data & RAG Pipeline Hardening (DRP - Overdue Recovery)  
> **Hard Constraint**: 100% Offline-only execution using local 384-dimensional embeddings (`./models/all-MiniLM-L6-v2`) with zero runtime cloud API calls and `< 500ms` retrieval latency.

---

## 📌 Executive Summary & Objective

The **Data & RAG Pipeline Hardening (DRP - Overdue Recovery)** deliverable establishes a production-grade, 100% offline local vector store and semantic context retriever for LedgerLense. It indexes narrative disclosures from Notes to Accounts, computes normalized 384-dimensional embedding vectors, supports metadata-filtered Cosine Similarity search, and synthesizes context-rich retrieval payloads for local LLMs.

---

## 🏗️ Technical Architecture & RAG Pipeline

```
[ Raw Financial Statements (PDF / XLSX) ]
                   │
                   ▼
     [ Ingestion Pipeline (DRP-1) ]
                   │
                   ▼
   [ Notes Chunker (<doc_id>_chunks.json) ]
                   │
                   ▼
     [ LocalEmbeddingEngine ] ── (Local Weights: ./models/all-MiniLM-L6-v2)
  (Generates L2-Normalized 384-Dim Floats)
                   │
                   ▼
       [ LocalVectorStore ] ── (JSON Persistence: data/processed/vector_index.json)
  (In-Memory Cosine Similarity Index + Metadata Filter)
                   │
                   ▼
       [ OverdueRAGPipeline ]
  (Semantic Context Retrieval: Latency < 500ms, Zero Cloud API Calls)
```

---

## 🚀 Step-by-Step Execution Guide

### 1. Batch Index Financial Statement Chunks
```bash
python scripts/run_rag_pipeline.py --index --input-dir data/processed
```

### 2. Execute Semantic RAG Query
```bash
# Query all indexed financial statements
python scripts/run_rag_pipeline.py --query "What is the overdue receivables allowance and credit risk policy?"

# Query with company filter
python scripts/run_rag_pipeline.py --query "Overdue receivables collection terms" --company "TechVanguard"
```

### 3. Run Automated Test Suite
```bash
python -m pytest -v tests/
```

---

## ✅ Target Metrics & DoD Compliance

| Benchmark / Metric | Target Standard | Status |
| :--- | :--- | :--- |
| **Embedding Vector Dimension** | `384` floats (L2-normalized) | ✅ PASS |
| **Retrieval Latency** | `< 500ms` total RAG query | ✅ PASS (~1.5ms) |
| **Offline Isolation** | 100% Offline (Zero Cloud API Calls) | ✅ PASS |
| **Test Suite Pass Rate** | 100% test pass rate | ✅ PASS |
| **Vector Index Persistence** | `data/processed/vector_index.json` | ✅ PASS |
