# LLM Financial Summary & Insight Engine (LIG - Overdue Recovery)

> **Product**: LedgerLense  
> **Sprint**: Sprint 1  
> **Deliverable**: LIG-1. Local Quantized LLM Setup (Offline Ollama Llama-3.2) & Overdue Recovery Engine  
> **Hard Constraint**: 100% Offline-only, low-resource local models (quantized Llama-3.2 via Ollama) — **ZERO cloud API calls at runtime**.

---

## 📌 Executive Summary & Objective

The **LLM Financial Summary & Insight Engine (LIG - Overdue Recovery)** parses ingested financial statements and narrative Notes to Accounts, evaluates liquidity risks and accounts receivable aging, generates deterministic overdue accounts collection plans, and synthesizes executive financial health summaries using local quantized Llama-3.2.

---

## 🏗️ Technical Architecture & Pipeline

```
[ Incoming Data / Ingested Financial Statement ]
                       │
                       ▼
      [ Validation & Preprocessing Layer ]
  (Pydantic v2 schemas: FinancialSummaryRequest)
                       │
                       ▼
     [ Core AI/ML Processing Engine (LIG) ]
     ├── Quantized Local Model: Llama-3.2 (Ollama / offline fallback)
     ├── Overdue Accounts Aging & Collection Planner
     └── Financial Health & Liquidity Risk Evaluator
                       │
                       ▼
       [ Verification & Quality Gate ]
  (Automated Sanity Tests & Zero Network Isolation)
                       │
                       ▼
   [ Structured JSON Output / Insights Dashboard ]
  (<statement_id>_insights.json: Overdue accounts, metrics, risk flags)
```

---

## 📋 Features & Specifications

- **Strongly-Typed Data Contracts**: Built using Pydantic v2 (`OverdueAccount`, `FinancialInsight`, `OverdueSummaryMetrics`, `FinancialSummaryResult`).
- **Local Quantized LLM Execution**: Interfaces with local Ollama (`llama3.2`) daemon (`http://localhost:11434`) using pre-cached model configs in `./models/ollama_llama3.2_config.json`.
- **Offline Fallback Guarantee**: If local daemon is offline or in socket-isolated CI environments, executes deterministic quantized local analysis without network dependencies.
- **Overdue Receivables Analytics**: Categorizes overdue accounts into risk tiers (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), computes collectible recovery estimates, and recommends actionable collection plans.
- **Latency Guarantee**: Operates under strict low-resource runtime budgets (< 500ms execution latency).

---

## 🚀 Step-by-Step Execution Guide

### 1. Ingest Sample Financial Statements
```bash
python scripts/generate_sample_data.py
python scripts/run_ingestion.py --input-dir data/raw --output-dir data/processed
```

### 2. Run Financial Insight & Overdue Recovery Engine
```bash
# Process all ingested financial statements in batch
python scripts/run_insight_engine.py --input-dir data/processed --output-dir data/processed

# Process a single file
python scripts/run_insight_engine.py --file data/processed/stmt_sample_1_techvanguard_fy24_structured.json
```

### 3. Run Automated Test Suite
```bash
python -m pytest -v tests/
```

---

## ✅ Definition of Done (DoD) & Target Metrics

| Requirement / Metric | Target Standard | Status |
| :--- | :--- | :--- |
| **Code Syntax & Errors** | Zero runtime unhandled exceptions | ✅ PASS |
| **Execution Latency** | `< 500ms` total pipeline runtime | ✅ PASS |
| **Offline Isolation** | Zero outbound cloud API calls | ✅ PASS |
| **Unit Test Coverage** | 100% test pass locally | ✅ PASS |
| **Output JSON Format** | `<statement_id>_insights.json` valid schema | ✅ PASS |
