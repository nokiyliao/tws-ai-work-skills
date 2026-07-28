---
name: nokiy-deck-orchestrator
description: Orchestrate Nokiy presentation production from PDF, Word, PPTX, notes, or structured briefs. Use for creating, rebuilding, revising, or validating customer-facing decks that require mandatory Humanizer copy review, editable PPTX construction, Codex-PPT-led visual acceptance, mechanical QA, asset traceability, and optional PDF input or output review.
---

# Nokiy Deck Orchestrator

Coordinate the presentation pipeline. Do not duplicate or weaken the delegated
skills. Keep the source authority, copy lock, visual acceptance, and mechanical
acceptance as separate gates.

## Required Skills

Read the selected skill completely before using its phase:

- Copy: `~/.codex/skills/humanizer-zh-tw/SKILL.md`
- Editable build and mechanical QA:
  `~/.codex/skills/nokiy-presentation-generator/SKILL.md`
- Visual style, sample, and acceptance:
  `~/.codex/skills/codex-ppt/SKILL.md`
- PDF input, explicit PDF output, and PDF rendering review:
  `~/.codex/skills/pdf/SKILL.md`

Read `references/pipeline-contract.md` before starting a deck run.

## Route

Choose one build mode. Do not mix final assembly engines.

- `editable` (default): build the final PPTX with
  `nokiy-presentation-generator`. Use Image2 only for text-free concept assets.
- `image`: use `codex-ppt` only when the user explicitly accepts full-slide
  image pages and their editability limitation.
- `revision`: patch only the user-authorized slides or objects. Preserve all
  untouched content and locked assets.

`codex-ppt` is the visual acceptance authority in every mode. In editable and
revision modes, apply its sample, rendering, inspection, and repair discipline
to the rendered PPTX; do not use its image-only assembly engine.

## Mandatory Pipeline

1. Initialize run state with `scripts/deck_pipeline_state.py init`.
2. Read sources and establish authority. Use `pdf` for PDF extraction and page
   rendering. Do not create a PDF output unless the user asks in the current
   request.
3. Confirm or prepare the slide outline. For a named-customer proposal without
   an approved outline, route content strategy through
   `tws-customer-proposal-pipeline` before continuing.
4. Run the Humanizer gate before layout:
   - Review every model-authored title, visible label, table cell, diagram node,
     footer, closing line, and new speaker note.
   - Preserve exact user-locked copy, numbers, units, names, model numbers,
     technical terms, quotations, and source citations. Flag them; do not
     silently rewrite them.
   - Save the accepted copy and mark the `copy` phase passed. No build may start
     from draft copy.
5. For a net-new deck, use the Codex-PPT outline/style/sample gates. A revision
   may mark `sample` skipped only when the existing deck is the approved visual
   reference.
6. Build the selected output mode. Editable mode must keep text, charts, tables,
   labels, and diagrams editable. Logos and product proof use official or
   user-provided assets, never generated imitations.
7. Run Codex-PPT-led visual acceptance:
   - Render every slide to PNG.
   - Inspect the cover and every slide at full size.
   - Compare against the approved outline, style sample, source assets, and
     page role.
   - Repair or regenerate failed pages and repeat until the visual report passes.
8. Run Nokiy mechanical QA after visual acceptance passes. It retains blocking
   authority for package integrity, editability, copy rules, minimum font size,
   text fit, title-zone intrusion, overlap, asset registry, locked assets, OCR,
   media, and numeric/source consistency.
9. Use `pdf` for final export and page review only when explicitly requested.
10. Run `scripts/deck_pipeline_state.py check`. Deliver only when it reports
    `PASS`.

## Acceptance Authority

- Visual composition, hierarchy, consistency, image quality, crop, distortion,
  density, and sample fidelity: `codex-ppt` is primary.
- Copy naturalness: `humanizer-zh-tw` is primary.
- Source authority, exact locked copy, factual/numeric accuracy, editability,
  geometry, package health, and asset identity:
  `nokiy-presentation-generator` is blocking.
- PDF rendering defects: `pdf` is blocking when PDF is in scope.

Any blocking failure prevents delivery. A visual pass cannot override a factual,
editability, overlap, or asset-authority failure.

## State Tool

Use a run-specific scratch directory:

```bash
python scripts/deck_pipeline_state.py init --run-dir <scratch> --mode editable --source <file>
python scripts/deck_pipeline_state.py set --run-dir <scratch> --phase copy --status pass --evidence <copy-file>
python scripts/deck_pipeline_state.py show --run-dir <scratch>
python scripts/deck_pipeline_state.py check --run-dir <scratch>
```

Record real evidence files. Chat statements are not completion evidence.

