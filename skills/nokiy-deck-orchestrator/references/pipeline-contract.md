# Deck Pipeline Contract

## Output Modes

| Mode | Final builder | Visual acceptance | Use when |
|---|---|---|---|
| `editable` | Nokiy generator | Codex-PPT rubric on rendered slides | Default customer deck |
| `image` | Codex-PPT | Codex-PPT native workflow | User accepts full-slide images |
| `revision` | Nokiy generator | Codex-PPT rubric against existing deck | Patch an approved deck |

Never describe an image-mode deck as fully editable. Never assemble one final
deck with both builders.

## Required Run Artifacts

```text
<run-dir>/
  deck_pipeline_state.json
  input.json
  research/
    source-snapshot.json
    source-notes.md
  proposal/
    customer-profile.json
    deck-requirements.json
    proposal-content.json
  outline.md
  copy/
    source.md
    humanized.md
    copy-lock.json
  assets/
    selection-manifest.json
    verification-receipt.json
    visual-plan.json
    registry.json
  rendered/
    slide-01.png
  visual_qa.md
  mechanical_qa.txt
  build_note.md
  build-manifest.json
  final.pptx
  deployment-receipt.json
  registration-receipt.json
  download-readback.json
```

File names may be more descriptive, but each phase must record an existing
evidence path in `deck_pipeline_state.json`.

## TWS Case Identity

Use `lead_id` as the immutable case key. Copy the formal company name and case
facts from the source snapshot into `input.json`. Validate it with
`tws-input.schema.json`. Record aliases separately and never use them to change
the formal customer identity.

## TWS Asset Gate

Generate `selection-manifest.json` from the customer profile and deck
requirements. For internal runs, first materialize it from the controlled
read-only asset service with `scripts/remote_asset_library.py`; preserve the
remote verification receipt. The client must
validate the catalog SHA-256 returned by the service and the catalogued SHA-1
for every downloaded asset. Any transport, manifest, identity, or digest error
blocks the build. The build may access only assets listed in the verified
manifest.

The registry retains asset ID, relative path, digest, evidence level, allowed
use, reuse scope, and the slide where a designer placed it. Selection does not
assign a slide. Official, concept, and `customer_only` boundaries are blocking
rules. `customer_only` never controls HTTP authorization for company members;
The public Tunnel endpoint exposes only the deliberately read-only catalog API.

Every TWS deck, including a generic company introduction without a customer
case, must produce `tws_deck_visual_plan_v1`. It maps every slide to one of:
`official_asset`, `concept_asset`, `generated_concept`, `editable_diagram`,
`data_visual`, or an explicitly justified `typography_only` exception. Run
`scripts/validate_visual_plan.py` before build and again after build with the
asset registry and final PPTX. The second pass verifies actual per-slide media
relationships, not merely the presence of files under `ppt/media`.

The Markdown fast builder is not a TWS final builder. It is allowed only for
non-TWS `general` internal drafts.

## Copy Gate

Apply Humanizer to all newly authored customer-visible copy and speaker notes.
Do not apply it to prompts, code, paths, build notes, or QA diagnostics.

Lock these tokens before rewriting:

- exact user-provided copy marked as fixed;
- company, product, model, and software names;
- numbers, units, dates, currency, dimensions, capacity, and performance data;
- engineering terms required by the source;
- quotations and source citations.

The accepted `humanized.md` is the copy authority for the build. Post-build text
extraction must not introduce unreviewed customer-visible text. When a revision
changes only selected slides, Humanize changed and newly created text; preserve
untouched approved slides.

## Codex-PPT-Led Visual Acceptance

Render all final slides and inspect them as images. The visual report must list
each slide and a verdict. Check:

1. The slide matches its outline role and approved sample.
2. The visual style is consistent without repeating one layout mechanically.
3. The title and decision point are readable within three seconds.
4. Image2 assets have no fake text, logo, watermark, product distortion, or
   unexplained crop.
5. Official logos and product images retain correct proportions and identity.
6. The page is neither crowded nor empty without purpose.
7. Visuals carry the slide; prose does not substitute for a diagram or image.
8. Text hierarchy, spacing, margins, alignment, and contrast are coherent.
9. No accidental page number, prompt text, debug text, or internal instruction
   is visible.
10. The full deck has a coherent rhythm across cover, content, comparison,
    process, architecture, and closing pages.

Set `visual_qa` to pass only after failed pages are repaired and re-rendered.

## Mechanical Acceptance

Run the Nokiy generator QA after visual QA passes. Use customer-facing strict
gates for customer decks. Preserve its asset registry, build note, OCR, copy,
font, containment, overlap, title-zone, off-slide, and package checks.

## PDF Handling

- PDF input: render pages before relying on extracted text; record both text
  extraction and visual evidence.
- PDF output: only on explicit user request. Export from the final PPTX, render
  every page, and block delivery for clipping, substitution, broken glyphs,
  layout shifts, or page-count mismatch.
- When PDF is not requested, mark the `pdf` phase skipped.

## Completion Rule

Required pass phases: `source`, `outline`, `copy`, `build`, `visual_qa`, and
`mechanical_qa`. `sample` must be `pass` or an allowed `skipped`; `pdf` must be
`pass` when requested and `skipped` otherwise.

Both TWS workflows require `asset_selection`, `asset_verification`, and
`visual_plan`. Named-customer `tws-new-factory` acceptance also requires
`case_lock` and `proposal`. Platform publication additionally requires `deploy`,
`register`, and `readback`. Readback evidence binds the released PPTX digest to
the Mini file, database row, and platform download.
