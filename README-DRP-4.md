# DRP-4: Scanned Financial Statement OCR Fallback (Tesseract)

**Product**: LedgerLense | **Sprint**: Sprint 1 | **Status**: Production Ready

---

## 📌 Technical Overview

`DRP-4` implements a scanned PDF / low-density image page OCR fallback mechanism for LedgerLense. When standard `pdfplumber` digital text extraction fails to extract sufficient text density (`< 50` characters per page or missing tables), the system automatically triggers Tesseract OCR with deterministic layout fallback, guaranteeing zero unhandled runtime crashes.

---

## 🏗️ Architecture & OCR Fallback Pipeline

```
[ Financial Statement PDF Page ]
              │
              ▼
[ Digital Text Extraction (pdfplumber) ]
              │
              ▼
  [ Text Density Evaluation ] ── (Length >= 50 chars & Tables > 0?)
         │           │
       (Yes)        (No)
         │           │
         ▼           ▼
[ Standard ]   [ Tesseract OCR Fallback ]
 [ Parsing ]         │
                     ├── (Tesseract Binary Available)  ──► [ Tesseract Image OCR ]
                     └── (Missing Binary / Error)       ──► [ Deterministic Layout Fallback ]
```

---

## 📄 Data Contracts & Schemas (`src/extractors/ocr_fallback.py` & `src/models.py`)

- `OCRExtractionConfig`: Configuration contract holding `min_text_density_chars`, `language`, `resolution_dpi`, and `timeout_sec`.
- `OCRFallbackResult`: Output schema containing `ocr_text`, `is_fallback_triggered`, `ocr_method`, `latency_ms`, and `error_message`.
- `ExtractedRawData.is_ocr_fallback_used`: Boolean flag set to `True` when any page in a PDF document requires OCR fallback extraction.

---

## 🧪 Verification & Automated Testing

Run all automated unit tests and DoD test suites:

```bash
python -m pytest -v tests/test_ocr_fallback.py tests/test_drp4_dod.py
```

Run full repository test suite:

```bash
python -m pytest -v tests/
```
