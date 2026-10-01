---
name: PDF Export
description: Create a checked PDF from an approved structured German report.
---
Use only after the report schema is validated. Never convert arbitrary uploaded executables.
1. Save a JSON report with exactly title (string), paragraphs (list of strings), table (rectangular matrix). Use only reviewed factual content.
2. Run `python scripts/ai_central_document_export.py --input report.json --output report.pdf` on the authorized GitHub Runner.
3. Validate the generated file and render/inspect pages before delivery; reject malformed pages and missing Unicode glyphs.
4. Store private result and SHA-256 in R2, return a controlled download. No direct public bucket link.
5. Never claim visual QA was completed unless the rendering check actually ran.
