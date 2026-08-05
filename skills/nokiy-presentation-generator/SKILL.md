---
name: nokiy-presentation-generator
description: Construct, restyle, fix, or verify editable PPTX files for Nokiy/TWS/TWSC/奔騰物流 — layout, python-pptx build scripts, Markdown-to-PPTX conversion, shared layout library, and mechanical QA. Use when the deck content/strategy is already decided and slides need to be built or revised. For deciding WHAT a proposal for a named target customer should say (research, opportunity thesis, slide logic), use tws-customer-proposal-pipeline, which delegates file construction to this skill.
---

# Nokiy Presentation Generator

Produce editable PPTX decks from briefs, Markdown, project files, or structured
analysis. Default to customer-facing TWS/TWSC decks that position 奔騰物流 as a
warehouse/logistics system integrator, not a single-equipment vendor.

## Canonical References

Read only what the task needs:

- `references/shared-governance.md` — authority order, deletion rule, revision
  modes, locked assets, hero-image governance, copy/numeric discipline, QA
  gates. **Single source of truth; always applies to customer-facing decks.**
- `references/assets-manifest.md` — every absolute path (scope assets, logos,
  product decks, output locations, Presenton). Never hard-code paths elsewhere.
- `references/tws-business-development-deck.md` — deck structures, module
  heuristics, customer-facing phrasing for TWS development decks.
- `references/tws-business-scope.md` — TWS positioning, product lines,
  capability map, signal translation.
- `references/markdown-format.md` — `slides.md` format for the converter.
- `references/customer-copy.md` — concise customer-facing copy method, title
  budgets, visual-first page structure, short labels, and AI-style sentence
  shapes to remove.
- `~/.codex/skills/humanizer-zh-tw/SKILL.md` — mandatory review for
  every newly authored or changed customer-visible line and speaker note.
- `data/banned_terms.json` — mode-keyed banned/discouraged terms (shared with
  `scripts/qa_check.py`).
- `data/copy_rules.json` — human-copy gates for title length, weak title
  patterns, and AI/marketing-fluff terms scanned by `scripts/qa_check.py`.
- `data/asset_registry.schema.json` — deck asset provenance registry schema for
  generated/user/official images and logo/product usage gates. Customer-facing
  decks with embedded images must provide the registry to QA.

## Route

- Named customer proposals: if the user names a target customer and no
  approved slide plan / `slides.md` / revision spec is provided, first use
  `tws-customer-proposal-pipeline`. This skill consumes the pipeline handoff or
  user spec and builds/revises the PPTX; it does not invent the customer thesis.
- High-polish customer-facing decks: use the installed Codex `Presentations`
  skill when available, then apply the TWS content rules here.
- Fast internal decks or Markdown conversion: `scripts/markdown_to_pptx.py`.
- Custom python-pptx builds: import `scripts/tws_pptx.py` (see below) instead
  of re-implementing layout helpers.
- Self-hosted platform requests only: Presenton (paths and run commands in
  `assets-manifest.md`).

## Workflow

1. Confirm the input contract: approved slide plan, user Markdown spec,
   annotated deck comments, existing deck revision scope, or pipeline handoff.
   If the task needs customer research, opportunity thesis, or slide logic,
   route to `tws-customer-proposal-pipeline` first.
2. Classify revision/build mode and scope per `shared-governance.md`.
3. Read `references/customer-copy.md` and
   `~/.codex/skills/humanizer-zh-tw/SKILL.md`, then write or consume a concise
   `slides.md` (one slide per `---` section). Every visible line must be
   short customer-facing copy. Default to a visual, flow, map, comparison, or
   product image with editable labels; do not write the speaker script into
   visible text. Put detailed explanation, design intent, prompts,
   implementation notes, source reasoning, and QA notes only in speaker notes
   or the private build note.
   The deck should read like a finished proposal, not a scaffold. Run the
   Humanizer pass before layout and treat the accepted copy as locked input.
   Reject formulaic AI sentence frames in both visible copy and speaker notes,
   including title phrasing built on `先＋動作`, `先……再……`, `不是……而是……`,
   `不只是……而是……`, `不只……`, `不僅……而且……`, and `真正的……`. State the
   condition, action, evidence, or result directly.
   Preserve exact user-locked wording, numbers, units, names, model numbers,
   technical terms, quotations, and citations. For patch revisions, review
   only changed or newly created text; do not rewrite untouched approved slides.
4. Build the PPTX. For custom builds:

   If the pipeline handoff includes an asset selection manifest, verify it
   before reading, copying, or embedding any selected asset. A failure stops
   the build; never replace the failed asset silently or select by filename:

   ```bash
   python3 <asset-library>/verify_assets.py \
     --library <asset-library> --selection <scratch>/asset-selection.json
   ```

   The manifest lists candidates only. Decide placement during slide design,
   within each asset's `allowed_use`: `official` is product evidence only,
   `concept` is scenario illustration only, and `customer_only` is valid only
   for the matching customer.

   ```python
   import os
   import sys
   skill_root = os.environ.get("CODEX_HOME", os.path.expanduser("~/.codex"))
   sys.path.insert(0, os.path.join(skill_root, "skills", "nokiy-presentation-generator", "scripts"))
   from tws_pptx import *   # tokens, add_slide, add_card, add_flow, qa-safe fonts
   ```

   `tws_pptx` enforces East-Asian typefaces, readable font minimums, disabled
   default shadows, and the protected title zone (`add_slide` returns the
   content-start y). Use `set_fill_alpha()` for transparency —
   `fill.transparency = N` is a silent no-op in python-pptx. For vertical
   card groups, use `add_card_stack()` or calculate each card's returned
   actual height; do not hard-code the next card's y position after an
   auto-expanding card.
5. Extract final PPTX text and confirm that no unreviewed visible copy was
   introduced by templates, reused slides, or automatic labels. Then run the
   mechanical QA gate and the visual checks for the chosen QA level
   (`shared-governance.md`):

   ```bash
   uv run --with python-pptx python \
     "${CODEX_HOME:-$HOME/.codex}/skills/nokiy-presentation-generator/scripts/qa_check.py" \
     final-deck.pptx --mode customer_facing --expect-slides 12 \
     --strict-zone --strict-overlap --strict-discouraged --strict-copy --min-font 10 \
     --build-note scratch/build_note.md \
     [--asset-library <asset-library> \
      --asset-selection-manifest scratch/asset-selection.json] \
     [--locked-asset assets/xxx.png] [--asset-registry assets/registry.json] \
     [--rendered-dir rendered_slides --ocr-rendered] [--allow-video]

   Render cross-platform before visual/OCR QA when the host has PowerPoint COM
   or LibreOffice plus Poppler/PyMuPDF:

   ```bash
   python scripts/render_slides.py deck.pptx --output rendered_slides
   ```
   ```

   It checks package integrity, slide count, editable text, banned/discouraged
   terms, human-copy smells, minimum font sizes, estimated text fit,
   title-zone intrusion, text/container containment, visible-object overlaps,
   locked-asset hashes, asset provenance and media coverage, build-note
   presence, optional rendered-slide OCR, and embedded video. Fix failures;
   layout exceptions must include `--layout-exception-reason` and are reported.
6. Keep a build note in the scratch folder (contents listed in
   `shared-governance.md`). Output paths and filename patterns are in
   `assets-manifest.md` — use a thread-scoped scratch directory and specific
   filenames, never `output.pptx`.
7. PDF only on explicit request (policy in `shared-governance.md`).

## Markdown Conversion

```bash
PATH="$HOME/.local/bin:$PATH" uv run --with python-pptx \
  python "${CODEX_HOME:-$HOME/.codex}/skills/nokiy-presentation-generator/scripts/markdown_to_pptx.py" \
  slides.md final-deck.pptx --title "Deck Title"
```

Read `references/markdown-format.md` first for nontrivial decks.

## Style Defaults

- Editable text boxes and shapes; never slide-sized screenshots.
- Quiet industrial business styling (tokens in `tws_pptx.py`): off-white
  background, charcoal text, BT orange-red as the primary visual accent, zinc-
  silver structural elements, white cards, hairline borders, large numbers.
- Titles are short viewing instructions, not report headings. Prefer 4–12
  Chinese characters: `確認包裝條件`, `棧板定位`, `量測通道`. Avoid `先＋動作`, long claims,
  slogans, and sentences joined by `、` or `｜`.
- Protect the title/subtitle zone: body content starts at the y returned by
  `add_slide()`. Align card tops on one baseline; shorten copy or move the
  diagram down rather than overlapping text. Never put accent lines under
  titles.
- For vertically stacked cards, use `add_card_stack()`; if a card's height is
  auto-expanded, the following card must be pushed down by the returned actual
  height plus a visible gap.
- Make the visual carry the page: reserve roughly 60–80% of the body for an
  image, process, map, comparison, or architecture. Use two to four short
  labels attached to it. Do not add a paragraph to fill unused space.
- Use `references/customer-copy.md` before drafting. Visible copy is a title,
  labels, numbers, and confirmation prompts; speaker notes carry the reasons,
  caveats, and explanation. Body text should target 11–13pt; captions may be
  8.5–9pt. Split the slide instead of shrinking text.
- Real TWS logos and product/project photos (paths in `assets-manifest.md`)
  beat generated art. Hero/cover and Image 2.0 style rules are in
  `shared-governance.md`; default generated visuals are low-realism flat
  business illustrations, not photorealistic warehouse scenes.
- Cards only for repeated items, metrics, comparisons, or capability maps.
- For the TWS service-scope page, reuse the v0.7 overlay master (see
  `assets-manifest.md`); keep labels and leader lines editable.
- Lead with the user-corrected product lines when products are named: Toyota
  Material Handling group brands, Modula, MBB, Galaxis, AiTEN, Geek+, rack
  systems, FastLINK, LionsBot.
- Copy and numeric-claim discipline: `shared-governance.md` +
  `data/banned_terms.json` + `data/copy_rules.json`.
- Formulaic contrast/reveal structures listed in `customer-copy.md` are hard
  failures under `--strict-copy`; this includes variants in speaker notes.
- Never call `add_image()` with both width and height. Use
  `add_image_contain()`/`add_logo()` so logos and product images cannot be
  stretched or cropped accidentally. Fixed-height helpers raise when copy
  cannot fit; shorten or split the slide instead.
