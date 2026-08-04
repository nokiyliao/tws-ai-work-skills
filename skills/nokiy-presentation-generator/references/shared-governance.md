# Shared Deck Governance (Canonical)

This file is the single source of truth for authority order, revision rules,
copy discipline, image governance, and QA gates. Both
`nokiy-presentation-generator` and `tws-customer-proposal-pipeline` point here.
Do not restate these rules in other files; link to this one.

## Contents

- Authority order and deletion
- Revision modes and locked assets
- Cover and generated-image governance
- Asset registry and OCR
- Copy discipline and human-copy method
- Build note and QA gates
- PDF policy

## Authority Order

When sources conflict, use this priority:

1. Latest explicit user instruction in the thread.
2. User-provided Markdown spec, Google Drive file, annotated PPTX comment, or
   named local deck.
3. The existing deck being revised.
4. User-provided product/equipment photos and named local files.
5. Local TWS/TWSC authority decks, logos, and product folders
   (see `assets-manifest.md`).
6. Official customer/vendor/public sources.
7. Generated images, for conceptual or de-identified visuals only.

A user-provided Markdown spec is a contract: preserve page count, filenames,
footer text, exact copy, banned strings, and `do not change` areas unless the
user later overrides them.

**Deletion is authoritative.** When a newer spec, comment, or instruction
removes content, never reintroduce it from older decks, templates, memory,
retrieval results, or generated suggestions.

## Revision Modes

Classify scope before editing. Revision is patch-only by default; existing
customer-approved slides are immutable unless changed by explicit user
instruction, PPTX annotation, or authority Markdown.

- `Text-only`: preserve layout and assets. Light QA.
- `Asset swap`: preserve slide logic; lock and verify replacement assets.
  Full QA when customer-facing.
- `Spec-driven revision`: implement the spec literally before optional
  improvements. Full QA for customer-facing decks.
- `Rebuild`: only when the user asks for a new structure or the deck cannot be
  fixed safely.

For rewritten slides, keep a short change note: `old -> new -> authority source`.

## Locked Assets

If the user confirms an image is correct, lock it:

- Copy the authority image into the customer deck `assets/` folder.
- Record the path in the build script or build note.
- Verify the final PPTX contains it (`qa_check.py --locked-asset <path>`
  compares hashes against `ppt/media/*`).
- Never replace a locked asset with an earlier generated image or a similar
  substitute unless the user explicitly asks.
- Verify semantics, not only file identity: slide wording must match the
  visible equipment category, model family, configuration, and scenario.
  A correct hash with wrong slide text is still a QA failure.

## Cover And Hero Image Governance

Customer-facing covers and hero slides must not ship rough procedural artwork.

Acceptable final hero sources:

- user-provided or user-approved imagery.
- official/public imagery that is high-resolution and relevant.
- Image 2.0 generated de-identified concept imagery inspected at full size and
  copied into the deck `assets/` folder.
- established TWS service-scope assets (see `assets-manifest.md`).

Never use as final hero: code-drawn PIL/SVG/geometric placeholders, low-detail
vector mockups, screenshots or web thumbnails, or images with fake readable
text, logos, watermarks, UI gibberish, distorted equipment, or low resolution.
Programmatic placeholders are scratch comps only and block Standard/Full QA
until replaced.

When Image 2.0 is used: locate the saved image under
`$CODEX_HOME/generated_images/<thread-id>/`, copy it into the customer
`assets/` folder with a descriptive filename, record prompt + both paths in the
build note, reference only the copied file in the build script, add it to the
deck asset registry when it ships in the final deck, and inspect the source
image and the rendered cover at full size. Reject rough, cartoon-like,
low-resolution, watermarked, text-garbled, or disconnected imagery; regenerate
rather than lowering the bar.

After every Image 2.0 call, verify that the PNG exists on disk. If the image is
visible in chat but missing from `$CODEX_HOME/generated_images`, recover it from
the Codex session JSONL before continuing:

```bash
python /Users/nokiy/.codex/skills/nokiy-presentation-generator/scripts/recover_imagegen_outputs.py \
  --session /path/to/current/session.jsonl \
  --out /path/to/deck/assets/image2_recovered --limit-last 5 \
  --prompt-contains "distinctive scene phrase"
```

Then copy the selected recovered PNG into the customer deck `assets/` folder
with a stable descriptive filename and record both the recovery folder and final
asset path in the build note.

### Image 2.0 Default Style For TWS Decks

For TWS/Nokiy customer-facing decks, the default Image 2.0 style is a
low-realism flat illustration, not photorealistic warehouse imagery. This keeps
generated visuals aligned with editable PPTX diagrams and avoids the visual
disconnect of photo-like scenes beside business process maps.

Use this default for conceptual, de-identified, cover, chapter, WMS/WCS,
workflow, service-scope, or scenario visuals unless the user explicitly asks for
photorealism, official/product proof imagery, or a real-site image.

Prompt requirements:

- `flat vector-style illustration` / `low-realism business illustration`.
- off-white or warm-white background compatible with TWS deck styling.
- dark green, charcoal, muted gray, and warm orange accents.
- simplified warehouse, rack, WMS/WCS, dock, AGV/AMR, RF/PDA, service, or
  material-flow objects; clean linework and readable negative space.
- no photorealism, no glossy 3D render, no cinematic lighting, no stock-photo
  look.
- no readable text, fake labels, logos, watermark, brand names, or UI gibberish.
- no precise product/model claims unless the image is based on an official or
  user-approved product asset.

Default prompt skeleton:

`Create a 16:9 flat vector-style low-realism business illustration for a TWS warehouse/logistics presentation. Scene: <specific operational scenario>. Use an off-white background, simplified industrial objects, dark green and warm orange accents, clean linework, subtle depth only, and generous negative space for slide text. No photorealism, no glossy 3D rendering, no readable text, no logos, no watermark, no brand names, no fake UI labels.`

Do not use generated concept art as product proof. For equipment-selection
slides, official or user-provided product images remain higher authority than
Image 2.0 illustrations.

### Asset Registry And OCR

For customer-facing decks that include generated images, logo swaps, product
photos, or user-confirmed locked visuals, keep an `assets/registry.json` beside
the deck assets using `data/asset_registry.schema.json`. Required fields per
asset: `deck_asset_path`, `source_type`, `role`; add `sha1`, `original_path`,
`authority`, `allowed_use`, and `prompt` when known.

Run `qa_check.py --asset-registry assets/registry.json --build-note
<scratch>/build_note.md` before delivery. In customer-facing mode, the registry
must cover every embedded image; an omitted registry or build note is a QA
failure, not an optional warning.
Generated assets may be used for `hero`, `concept`, `workflow`, or
`deidentified` roles only. They must not be used as `logo`, `product_proof`,
`equipment_selection`, `model_exterior`, or `real_site_evidence`.

When a cover/hero or generated visual is part of the final customer deck,
render the affected slide(s) to PNG and run `qa_check.py --rendered-dir
<folder> --ocr-rendered`. OCR hits for banned prompt/debug/watermark terms are
blocking failures. OCR is a supplemental gate, not a replacement for full-size
visual inspection; distorted Chinese, fake symbols, logos, and product-shape
errors still require manual inspection.

## Copy Discipline

### Mandatory Humanizer Gate

Read `/Users/nokiy/.codex/skills/humanizer-zh-tw/SKILL.md` before drafting or
rewriting customer-visible copy. Every model-authored or changed title, label,
table cell, diagram node, footer, closing line, and speaker note must pass that
review before layout begins. Preserve user-locked wording, numeric claims,
units, names, model identifiers, technical terms, quotations, and citations.
Flag concerns in locked copy instead of silently rewriting it.

The accepted Humanizer output is the copy authority for the build. After PPTX
generation, extract final text and verify that templates, reused slides, or
automatic labels did not reintroduce unreviewed copy. For patch revisions,
apply this gate only to changed or newly created text and keep untouched
approved slides immutable.

Slides must read as written to the customer, not about the deck. The
machine-readable term lists live in `data/banned_terms.json`; the QA script
scans the final PPTX text with them. Human-copy rules live in
`data/copy_rules.json`. Summary:

- No proposal self-commentary, internal-control language, or review-status
  wording in customer decks.
- No design prompts, production instructions, image-generation prompt text,
  layout intent, implementation notes, QA notes, source reasoning, or build
  diagnostics in customer-visible slides. Put those in the build note only.
- A `slides.md` file for a customer deck is output text, not planning text:
  every line must be acceptable if copied directly into the final PPTX.
- Phrase uncertain items as `會議確認項目` or `建議確認條件`.
- Prefer `追蹤項目` over `KPI`, `試行` over `PoC`,
  `第一步 / 第二步 / 第三步` over `Phase 1/2/3` in early customer decks.
- Banned words are mode-specific. Do not delete necessary engineering terms
  that are part of a customer's specification, model name, or explicit
  user-provided copy. When in doubt, rewrite the sentence.
- Keep the page visual: one short title, one visual or flow, and two to four
  editable labels. Do not put the speaker script, rationale, caveats, or a
  long confirmation list on the slide. Put details in speaker notes, an
  appendix, or the private build note.

### Human Copy Style

Write like a person preparing a customer meeting, not a model summarizing a
proposal. Before building the PPTX, run a copy pass:

- Titles should be short viewing instructions, ideally 4-12 Chinese characters
  and normally below the `copy_rules.json` title limit.
- Use labels made of concrete nouns and verbs: `找料`, `包裝`, `補料`, `儲位`,
  `回報`, `確認`, `切片`, `冷卻`, `放行`.
- Cut abstract packaging words: `主軸`, `藍圖`, `策略方向`, `整體方案`,
  `可視化`, `智慧化`, `數位轉型`, `打造`, `賦能`, `助力`.
- Do not write long title strings joined by `、` or `｜`. If a title needs more
  than one breath, split the slide or move detail into the subtitle.
- Prefer short labels over customer-visible outcome sentences:
  `量測通道` beats `AGV 車型評估與現場適用條件`;
  `庫存｜任務｜設備` beats `WMS 作業可視化底層建置`.
- Body copy should be optional. If the visual is clear without the sentence,
  delete the sentence. Never use text to explain an arrow that can be drawn
  clearly.
- Use `references/customer-copy.md` for the drafting pass. Its title patterns,
  concrete-verb rules, and spoken-language test are the preferred way to remove
  generic AI-style copy before building the PPTX.

**Numeric claims.** Never invent business numbers. ROI, manpower reduction,
throughput, accuracy, utilization, payback, storage increase, or ESG benefit
must trace to user data, authority specs, or approved sources. Otherwise write
them as confirmation or tracking items (e.g. `以覆膜完成率與重工件數追蹤`).

## Build Note

For every customer-facing deck, keep a brief build note in the scratch output folder
(never in customer slides): deck mode and audience, authority inputs, locked
asset paths, banned/replacement terms from the user or spec, output paths, and
QA level completed. Pass this note to `qa_check.py --build-note`; an empty or
missing note fails customer-facing QA.

## QA Gates

Run `scripts/qa_check.py` for the mechanical checks at every level, then add
visual inspection as required. Choose the lightest safe level.

### Light QA

Small text-only edits, no layout/asset changes:

- `qa_check.py <deck> --mode customer_facing --expect-slides N`
  (covers package integrity, slide count, editable text, banned-term scan,
  minimum font size, title-zone report, and visible-object overlap report).

### Standard QA

Ordinary customer deck builds and revisions:

- Everything in Light QA, but customer-facing decks must run strict layout and
  wording gates: `--strict-zone --strict-overlap --strict-discouraged
  --strict-copy --min-font 10`, plus `--locked-asset` for locked images and
  `--asset-registry` for every deck containing embedded images, plus
  `--build-note`. Do not use `--skip-overlap` or non-default title-zone skips
  without a written `--layout-exception-reason`; the exception is surfaced as
  a warning in the final QA output.
- Render all slides to PNG; inspect the contact sheet rhythm.
- Inspect the full-size cover/hero render before later steps.
- Run rendered-slide OCR on final cover/hero/generated-image slides when they
  are used in a customer-facing deck.
- Inspect the weakest full-size slides; always include WMS/WCS architecture,
  three-column diagrams, multi-step process flows, and dense tables.
- Confirm no unintended embedded video (qa_check reports media).

### Full QA

New high-polish decks, customer decision decks, Drive/Google review revisions,
image swaps, explicit PDF deliverables:

- Standard QA, plus required full-size slide inspections.
- If the user explicitly requested PDF: verify page count matches, render and
  inspect the PDF cover at page size.
- Run Drive sync/link verification when requested.

### Decision Consistency QA

For customer decision decks and existing-customer improvement proposals:

- One consistent project scope definition across slides.
- Recommended equipment paths do not conflict across slides.
- Aisle width, rack height, load, throughput, WMS/WCS boundary, and AGV
  assumptions are consistent or explicitly marked as labeled alternatives.
- Every numeric claim traces to an authority source.
- Cross-slide contradictions are P0 failures even when each slide is
  individually valid.

### Blocking rules

- Any overlap between the title/subtitle area and body objects is a blocking
  visual failure (qa_check reports geometry; confirm visually).
- Any overlap between stacked cards, text boxes, diagrams, or product images is
  a blocking visual failure. Use `add_card_stack()` or returned object heights
  instead of fixed y offsets after auto-expanding content.
- A rough or placeholder cover is a blocking failure even if all text and
  package checks pass.
- Before the final response, state which QA level was completed and any
  limitation.

## PDF Policy

PPTX is the editable authority. Do not export PDF unless the user explicitly
asks in the current request. If a requested PDF export fails, report the
failure; a rendered-slides fallback PDF is acceptable only when the user asked
for a share/review PDF and is told the PPTX remains the source.
