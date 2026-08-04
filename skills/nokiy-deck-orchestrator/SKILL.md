---
name: nokiy-deck-orchestrator
description: The authoritative entry point for Nokiy and TWS presentations. Use whenever the user says 做簡報, 做新廠簡報, 建立客戶簡報, 做客戶提案, 重做簡報, 修改簡報, 更新簡報, 發布簡報, or asks to create, rebuild, revise, validate, publish, download, or register a PPT/PPTX/deck. Orchestrates case identity, proposal strategy, Humanizer review, verified asset selection, editable Presentations construction, visual and mechanical QA, versioned delivery, Mini upload, and presentation_jobs readback without allowing silent builder substitution.
---

# Nokiy Deck Orchestrator

## Natural-Language Triggers

Users do not need to name this skill. Treat these requests and close variants as
calls to this orchestrator:

- `幫我做新廠簡報`
- `幫台光電做客戶提案`
- `用案件 ID 9d1aa5423345 建立簡報`
- `重做星宇簡報`
- `修改這份 PPT`
- `檢查並發布簡報`

When a TWS customer or case ID is present, select the `tws-new-factory`
workflow automatically. Ask for missing identity data only when it cannot be
resolved from the case database or provided files.

Coordinate the presentation pipeline. Do not duplicate or weaken the delegated
skills. Keep the source authority, copy lock, visual acceptance, and mechanical
acceptance as separate gates.

For a TWS new-factory or named-customer proposal, this skill is the only
authorized entry point. A delegated skill that receives a request for a
complete TWS deck must return control here. Delegated skills cannot publish,
register, or declare the complete task successful.

## Required Skills

Read the selected skill completely before using its phase:

- Copy: `~/.codex/skills/humanizer-zh-tw/SKILL.md`
- TWS proposal strategy:
  `~/.codex/skills/tws-customer-proposal-pipeline/SKILL.md`
- Editable build and mechanical QA:
  `~/.codex/skills/nokiy-presentation-generator/SKILL.md`
- Visual style, sample, and acceptance:
  `~/.codex/skills/codex-ppt/SKILL.md`
- PDF input, explicit PDF output, and PDF rendering review:
  `~/.codex/skills/pdf/SKILL.md`

Read `references/pipeline-contract.md` before starting a deck run.

Run `scripts/preflight.py --workflow tws-new-factory` before creating a TWS
job. Any missing skill or asset-library dependency is a blocking failure.

For TWS work, validate `input.json` against
`references/tws-input.schema.json` and use the asset catalog at
`/Users/nokiy/Documents/TWS_AI_開發簡報/2026-08-03/asset-library/catalog.json`.

## TWS Authority Contract

- Resolve the formal customer name from the case record identified by
  `lead_id`. A prompt alias or speech transcription cannot replace it.
- Preserve the input snapshot, proposal content, selection manifest,
  verification receipt, build manifest, QA reports, deployment receipt, and
  readback evidence in one job directory.
- Run the catalog selector with the customer profile and deck requirements.
  Asset placement remains a design decision.
- Run `verify_assets.py --selection` before opening or embedding selected
  assets. Missing files, digest mismatches, role mismatches, and customer scope
  mismatches block the build.
- Official assets provide product or capability evidence. Concept assets
  provide scenario context. `customer_only` assets remain bound to their
  registered customer.
- Build editable TWS decks in the Presentations environment with job-specific
  content and reusable layout components. Do not silently substitute a generic
  `python-pptx` template when Presentations is unavailable.
- Publish after visual and mechanical QA pass. Register the released file with
  the same `lead_id`, then compare the approved file, Mini file, database
  digest, and downloaded file.

## Route

Choose one build mode. Do not mix final assembly engines.

- `editable` (default): for TWS customer decks, build the final PPTX in the
  Presentations environment. `nokiy-presentation-generator` remains the
  mechanical QA authority. Use Image2 only for approved text-free concept
  assets.
- `image`: use `codex-ppt` only when the user explicitly accepts full-slide
  image pages and their editability limitation.
- `revision`: patch only the user-authorized slides or objects. Preserve all
  untouched content and locked assets.

`codex-ppt` is the visual acceptance authority in every mode. In editable and
revision modes, apply its sample, rendering, inspection, and repair discipline
to the rendered PPTX; do not use its image-only assembly engine.

## Mandatory Pipeline

1. Initialize run state with `scripts/deck_pipeline_state.py init`. TWS jobs use
   `--workflow tws-new-factory` with `--lead-id`, `--customer-name`, and
   `--input`.
2. Read sources and establish authority. Use `pdf` for PDF extraction and page
   rendering. Do not create a PDF output unless the user asks in the current
   request.
3. Lock the case identity and route named-customer content strategy through
   `tws-customer-proposal-pipeline`. Record the customer profile, deck
   requirements, proposal content, and source notes as evidence.
4. Run the Humanizer gate before layout:
   - Review every model-authored title, visible label, table cell, diagram node,
     footer, closing line, and new speaker note.
   - Preserve exact user-locked copy, numbers, units, names, model numbers,
     technical terms, quotations, and source citations. Flag them; do not
     silently rewrite them.
   - Save the accepted copy and mark the `copy` phase passed. No build may start
     from draft copy.
5. Create and verify the asset selection manifest for TWS work. Mark selection
   and verification as separate phases. For a net-new deck, use the Codex-PPT
   outline/style/sample gates. A revision
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
10. Run `scripts/deck_pipeline_state.py check --target build` before local
    delivery. TWS platform publication also requires deploy, register, and
    digest readback evidence followed by `check --target publish`.

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

TWS initialization:

```bash
python scripts/deck_pipeline_state.py init \
  --run-dir <job-dir> --workflow tws-new-factory --mode editable \
  --lead-id <lead-id> --customer-name <formal-name> --input <input.json>
python scripts/deck_pipeline_state.py check --run-dir <job-dir> --target publish
```
