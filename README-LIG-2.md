# LIG-2. Dual-Persona Summary Engine (Client vs. Relationship Manager)

> **Product**: LedgerLense  
> **Sprint**: Sprint 1  
> **Deliverable**: LIG-2. Dual-Persona Summary Engine (Client vs. Relationship Manager)  
> **Hard Constraint**: 100% Offline-only execution with zero runtime cloud API calls and `< 500ms` latency.

---

## 📌 Executive Summary & Objective

The **Dual-Persona Summary Engine (LIG-2)** extends LedgerLense to deliver role-conditioned financial summaries and recovery action pathways:

1. **Client Persona (External)**: Transparent, plain-language financial health summary, clear payment settlement options (early payment credits, flexible installment plans), and self-service account resolution links.
2. **Relationship Manager Persona (Internal)**: Internal tactical risk analysis, collection urgency levels (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`), recommended credit limits, credit hold advisories, and step-by-step debt recovery negotiation playbooks.

---

## 🏗️ Architecture & Dual View Pipeline

```
                     [ Ingested Financial Statement Document ]
                                         │
                                         ▼
                          [ DualPersonaInsightEngine ]
                                         │
                    ┌────────────────────┴────────────────────┐
                    ▼                                         ▼
         [ Client View Generator ]                 [ RM View Generator ]
   - Plain-language executive summary       - Internal credit risk assessment
   - Self-service settlement options         - Collection urgency tier rating
   - Portal self-service quick actions       - Credit line limit recommendations
   - Reassuring customer support note        - Debt recovery negotiation playbook
                    │                                         │
                    └────────────────────┬────────────────────┘
                                         ▼
                    [ Structured DualPersonaSummaryResult ]
                    (<statement_id>_dual_insights.json)
```

---

## 🚀 Execution Guide

### Run Dual-Persona Engine via CLI
```bash
# Process all ingested financial statements in dual-persona mode
python scripts/run_insight_engine.py --persona dual --input-dir data/processed --output-dir data/processed

# Process a single document
python scripts/run_insight_engine.py --persona dual --file data/processed/stmt_sample_1_techvanguard_fy24_structured.json
```

### Run Test Suite
```bash
python -m pytest -v tests/
```

---

## ✅ Target Metrics & DoD Compliance

| Benchmark | Target Metric | Verified Status |
| :--- | :--- | :--- |
| **Dual Persona Support** | Client + RM distinct views | ✅ PASS |
| **Execution Latency** | `< 500ms` total pipeline | ✅ PASS (~60ms) |
| **Offline Isolation** | Zero cloud API calls | ✅ PASS |
| **Test Suite Coverage** | 100% test pass rate | ✅ PASS |
