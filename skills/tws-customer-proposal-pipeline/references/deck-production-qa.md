# Deck Production And QA Execution

Production handoff details for this pipeline. Canonical governance (authority
order, locked assets, hero-image rules, copy discipline, QA gate definitions)
lives in
`/Users/nokiy/.codex/skills/nokiy-presentation-generator/references/shared-governance.md`.
All asset and output paths live in
`/Users/nokiy/.codex/skills/nokiy-presentation-generator/references/assets-manifest.md`.
Do not restate either here.

## Skill Coordination

- `nokiy-presentation-generator`: deck writing, style defaults, `tws_pptx.py`
  layout library, `qa_check.py`.
- `presentations:Presentations`: high-polish editable PPTX rendering and visual
  QA when available.
- `imagegen`: customer-specific hero visuals or clean conceptual backgrounds
  only; never a substitute for a user-approved product image.

## Generator Handoff Contract

Before delegating construction, keep a compact handoff in the scratch build
note: mode, audience, slide count, slide order, per-slide customer-facing
claim, source IDs, TWS modules, locked assets, QA level, and whether Decision
Consistency QA is required. Do not pass internal thesis notes as slide copy.

## QA Execution

Run the mechanical gate first, on the final file:

```bash
PATH="$HOME/.local/bin:$PATH" uv run --with python-pptx python \
  /Users/nokiy/.codex/skills/nokiy-presentation-generator/scripts/qa_check.py \
  <final>.pptx --mode customer_facing --expect-slides <N> \
  --strict-zone --strict-overlap --strict-discouraged --strict-copy --min-font 10 \
  --build-note <scratch>/build_note.md \
  [--locked-asset <path> ...] [--asset-registry <assets/registry.json>] \
  [--rendered-dir <rendered_png_folder> --ocr-rendered] [--allow-video]
```

Then the visual layer per the QA level chosen from `shared-governance.md`:

- Render all slides to PNG and inspect the contact sheet.
- Inspect the full-size cover/hero before later steps.
- Always full-size-inspect WMS/WCS architecture, three-column diagrams,
  multi-step process flows, and dense tables — these hide title/subtitle
  overlap at thumbnail size. Any title-zone overlap is a blocking failure.
- Decision Consistency QA for decision/improvement decks: one scope
  definition, no conflicting equipment paths, consistent aisle/height/load/
  throughput/WMS-WCS-boundary assumptions (or labeled alternatives), every
  number traced to authority. Cross-slide contradictions are P0.

Layout-script warnings caused by full-slide background images may remain, but
never ignore visible overlap, clipped text, bad contrast, disconnected media,
or placeholder text.

Before the final response, state the QA level completed and any limitation.
Clean intermediate files from the scratch workspace, but keep the final PPTX,
deliberately reused assets, and the build note (it is the traceability record
required by `shared-governance.md`).

## Markdown Spec And Annotated Revision QA

When the user provides a Markdown spec, annotated PPTX comment, or review text:

- Extract hard constraints first: fixed slide count, fixed filename, exact
  copy, footer, banned strings, do-not-change areas. Add user-specified banned
  strings to the `qa_check.py` run via `--ban`.
- Preserve existing deck structure when requested; do not rebuild because the
  content could be improved.
- Apply comments on selected elements literally before adjacent improvements.
- Keep user-corrected images and product references stable across revisions;
  deletion and patch-only rules per `shared-governance.md`.

## Handoff Failure Handling

Do not let export or Drive issues silently degrade the artifact. PDF handling
applies only when the user explicitly requested PDF output:

- If PowerPoint AppleScript PDF export times out, try a shorter temp path,
  then fall back to high-resolution rendered slide images assembled into a PDF
  only if the user asked for a PDF deliverable — and say the PPTX remains the
  editable authority.
- If the Drive connector upload/import returns 403, copy files into the local
  Google Drive Desktop sync folder and verify with Drive search after sync.
- Report failed steps briefly in the final answer instead of hiding them.
