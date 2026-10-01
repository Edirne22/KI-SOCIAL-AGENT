---
name: Excel Export
description: Create a new structured Excel .xlsx workbook; protect against formula injection.
---
1. This skill creates a NEW workbook; it is NOT a fidelity-preserving editor of an uploaded XLSX.
2. Validate title/paragraphs/table JSON. Do not interpret model-proposed text as Excel formulas or macro code.
3. Run `python scripts/ai_central_document_export.py --input report.json --output report.xlsx`.
4. Check resulting XLSX integrity, row/column count and required formulas via a separate reviewer before delivery. XlsxWriter is the public hosted new-file exporter; a separate audited workbook editor is required for uploads.
5. Keep all result files private in R2. If Bülent requested Claude, require the strict Claude-only model route upstream or report unavailable. Never switch to Gemini on failure.
