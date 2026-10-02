# DRP-3: Client Multi-Tenant Data Isolation at RAG Layer

**Product**: LedgerLense | **Sprint**: Sprint 1 | **Status**: Production Ready

---

## 📌 Technical Overview

`DRP-3` implements strict multi-tenant client data isolation across the entire RAG pipeline. It guarantees zero cross-tenant data leakage (`cross_tenant_leakage_detected == False`) by mandating `tenant_id` scoping at both index time and retrieval time.

---

## 🏗️ Architecture & Security Model

```
[ MultiTenantQueryRequest ]
           │
           ▼
   [ TenantContext Authorization ] ── (Validates tenant_id claim)
           │
           ▼
[ Vector Store Search Engine ] ── (Filters candidate vectors WHERE tenant_id = query.tenant_id)
           │
           ▼
[ Security Gate Assertion ] ── (Asserts zero cross-tenant data leakage)
           │
           ▼
[ MultiTenantQueryResponse ]
```

### Key Security Safeguards
1. **Mandatory Tenant Scoping**: Every indexed `VectorChunk` requires a non-empty `tenant_id`.
2. **Metadata Filter Enforcement**: Vector similarity search in `LocalVectorStore` and `ChromaOfflineVectorStore` enforces `tenant_id` filtering before calculating/returning cosine similarity top-k results.
3. **Cross-Tenant Leakage Assertion**: `OverdueRAGPipeline.query_tenant_isolated()` checks all returned chunks against `TenantContext.tenant_id`. If any mismatched tenant chunk is detected, a `TenantAccessViolationError` is raised immediately.
4. **100% Offline Network Isolation**: Embedded MiniLM model runs locally with zero external API dependencies or network socket calls.

---

## 📄 Data Contracts & Schemas (`src/rag/schemas.py`)

- `TenantContext`: Security context containing `tenant_id`, `client_name`, `user_role`, and `permissions`.
- `MultiTenantQueryRequest`: Input payload requiring query text and authorized `TenantContext`.
- `MultiTenantQueryResponse`: Output payload containing tenant-scoped chunks, synthesized context, latency, and `cross_tenant_leakage_detected: bool`.
- `TenantAccessViolationError`: Exception raised when tenant authorization fails or data leakage occurs.

---

## 🚀 Usage & CLI Commands

### CLI Command Execution
Execute tenant-isolated RAG retrieval using `run_rag_pipeline.py`:

```bash
python scripts/run_rag_pipeline.py --query "What is the overdue trade receivables balance?" --tenant-id "tenant_sample_1" --top-k 3
```

---

## 🧪 Verification & Testing

Run all automated unit tests and DoD suites:

```bash
python -m pytest -v tests/test_tenant_isolation.py tests/test_drp3_dod.py
```
