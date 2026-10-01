---
name: Word Export
description: Create a Word .docx document from a reviewed structured report.
---
1. Validate the user's requested tone/content; preserve user-provided facts and references.
2. Produce exactly title/paragraphs/table JSON (see scripts/ai_central_document_export.py).
3. Generate `python scripts/ai_central_document_export.py --input report.json --output report.docx`.
4. Verify DOCX opens and render pages for visual QA before delivering a final user file.
5. Save privately to R2 and require user approval before sharing; no embedded scripts/macros.
