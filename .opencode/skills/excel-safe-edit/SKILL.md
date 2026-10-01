---
name: Excel Safe Edit (Preparation)
description: Requirements for editing an uploaded existing Excel workbook with a STRICT user-selected model.
slash: false
metadata:
  opencode/autoinvoke: false
---
NOT PRODUCT-ACTIVE. This is a gated engineering contract, not proof of finished XLSX upload editing.
1. Never overwrite the original workbook. Store original input and checksums privately and verify allowed extensions/file magic, zip size, macros, external connections.
2. If user requested Claude ONLY, choose an exact verified Anthropic Claude model (direct key or OpenRouter Claude route), never another model; absent verified inference means stop and explain.
3. Claude proposes changes, but a separate deterministic workbook editor must apply them while preserving existing formulas, chart references and formatting. Run real import/edit/export regression tests on diverse workbooks before enabling.
4. Validate every changed cell, formula/reference and rendered workbook. Return a new private file for human approval. No automatic publishing, GitHub merge or deployment.
