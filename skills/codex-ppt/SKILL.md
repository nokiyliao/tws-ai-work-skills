---
name: codex-ppt
description: Visual direction and blocking acceptance for presentation decks. Use when Codex must create a visual sample, review rendered PPT/PPTX slides, repair visual defects, validate image-mode slides, or decide whether a deck passes visual QA. For TWS customer decks, act as the visual authority inside nokiy-deck-orchestrator without replacing its editable builder, source checks, asset verification, or mechanical QA.
---

# Codex PPT

Own visual direction and rendered-slide acceptance. Judge pixels, composition,
hierarchy, image quality, and cross-slide rhythm. Do not claim source accuracy,
editability, package health, or publication readiness; those remain with the
orchestrator and `nokiy-presentation-generator`.

Read `references/visual-rubric.md` before reviewing a customer-facing deck.

## Authority Boundaries

- In `editable` mode, never rebuild the final deck as slide-sized images.
  Review the renderer output and return repair instructions to the editable
  builder.
- In `revision` mode, inspect changed slides at full size and compare untouched
  slides for accidental visual drift.
- Use `image` mode only after the user explicitly accepts that each page is a
  full-slide image with limited editability. State that limitation in delivery.
- A visual pass cannot override failed facts, copy, asset digest, editability,
  overlap, package, mechanical QA, deployment, or readback gates.
- Selection manifests identify eligible assets, not placement. Do not bypass
  `official`, `concept`, `customer_only`, or allowed-use boundaries.

## Workflow

1. Read the approved outline, humanized copy, source/asset notes, output mode,
   and any approved visual reference.
2. For a net-new deck, define a compact visual direction: palette, type scale,
   spacing, image treatment, diagram treatment, and page rhythm.
3. Build one representative sample slide before full production. Choose a page
   that exercises the real design system, not an easy title-only page. Record
   the approval evidence. A revision may skip the sample only when the existing
   approved deck is the reference.
4. After the builder produces the PPTX, render every slide to PNG. Never judge
   a deck from source code, extracted text, or thumbnails alone.
5. Inspect the cover and every slide at full size. Apply the blocking rubric in
   `references/visual-rubric.md` and record one verdict per slide.
6. Return exact repair instructions tied to slide number and object/region.
   Repair the editable source, rebuild, and re-render failed slides.
7. Repeat until every slide passes. Save both `visual_qa.json` and a concise
   `visual_qa.md` in the job directory.
8. Run `scripts/validate_visual_report.py` against the JSON report. Only then
   may the orchestrator mark `visual_qa` as passed and proceed to mechanical QA.

## Required Evidence

The job must preserve:

- approved outline and copy authority;
- sample image plus approval, or an allowed skip reason;
- rendered PNG for every final slide;
- `visual_qa.json` with one verdict per slide;
- `visual_qa.md` summarizing visual direction, failures, repairs, and final
  verdict;
- re-rendered evidence for every repaired slide.

Validate the machine-readable report:

```bash
python3 ~/.codex/skills/codex-ppt/scripts/validate_visual_report.py \
  <job-dir>/visual_qa.json --rendered-dir <job-dir>/rendered
```

Any missing slide image, missing verdict, reported failure, inconsistent final
verdict, or invalid sample status blocks completion.

## Repair Discipline

- Repair the smallest responsible source object or layout rule; do not flatten
  an editable slide to hide defects.
- Recheck the full page after every repair because text flow, crop, and spacing
  changes can create secondary defects.
- Prefer shorter approved copy, clearer grouping, and fewer objects over
  shrinking text or compressing margins.
- Preserve official logo/product proportions. Do not redraw logos or use
  generated imagery as product proof.
- Reject fake text, watermarks, malformed equipment, unexplained crops,
  duplicated objects, and broken physical continuity in generated images.
- Treat visible prompt text, debug labels, placeholders, internal disclaimers,
  and accidental page furniture as blocking leakage.

## Completion

Return `PASS` only when the final rendered set matches the final PPTX and every
slide has a passing verdict. Report unresolved defects plainly and leave the
orchestrator's `visual_qa` phase failed; do not substitute a weaker acceptance
claim.
