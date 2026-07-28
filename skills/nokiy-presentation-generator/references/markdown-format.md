# Markdown Deck Format

Use this format for fast editable PPTX generation.

For customer-facing copy, read `references/customer-copy.md` first. The
converter now rejects fixed text boxes whose estimated content cannot fit;
shorten the line or split the slide instead of using `--allow-dense`.

## Structure

- Separate slides with a line containing only `---`.
- Put one `#` heading at the top of each slide.
- Use short labels, not paragraphs. Put presenter-only detail in an HTML
  comment such as `<!-- speaker: explain the loading constraint -->`; comments
  are ignored by the converter and never appear on the slide.
- Use `![alt](path/to/image.png)` for local images.
- Keep each slide to one main idea.

## Layout Auto-Mapping

`markdown_to_pptx.py` picks each slide's layout mechanically — write slides.md
with this in mind:

- Slide 1 is always the dark cover (title + body/bullets joined as subtitle).
- A slide with an existing local image → image layout (first image right,
  up to 4 bullets left).
- Title containing `下一` / `步驟` / `流程` / `時程` / `排程` →
  3-step horizontal layout. Do not use `確認` alone to force a process layout.
- Otherwise 1–4 bullets → cards; 5 bullets → numbered list; 6+ bullets are
  too dense for a customer-facing slide and should be split.
- The first non-bullet body line after the title becomes an optional compact
  takeaway strip. Keep it short; omit it when the visual already carries the
  point.
- `--footer` sets the cover badge and per-slide footer; keep it
  customer-facing (default `TWS 奔騰物流`).

## Recommended Deck Shapes

Generic proposal deck:

1. Cover: customer, project, date
2. Problem / current state
3. Proposed solution
4. Layout or system overview
5. Key specifications
6. Schedule or implementation steps
7. Risks, assumptions, and required confirmations
8. Next actions

TWS new-factory business development deck:

1. Cover: customer, `新廠倉儲與運搬系統前期規劃建議`, TWS identity
2. Why now: the business trigger and why early warehouse planning matters
3. Initial operation reading: known facts and `初步觀察`
4. Integrated TWS solution map: site/dock, rack/floor, handling/fleet,
   automation/software, service
5. Suggested scenario path: staged solution modules matched to the customer
6. Technical checkpoints: floor, height, aisle, dock, safety, power, systems
7. TWS capability proof: integration breadth and implementation support
8. Next step: 30-60 minute planning discussion and data to prepare

Equipment comparison deck:

1. Decision summary
2. Comparison table
3. Option A
4. Option B
5. Cost / benefit / operational impact
6. Recommendation

## Writing Rules

- Titles should be short viewing instructions:
  `量測通道`, not `AGV 車型評估與現場適用條件`.
- Keep Chinese titles short; if the title needs commas, slash marks, or more
  than one phrase, move detail to a note, appendix, or another slide.
- Bullets should be factual and concise.
- Customer-facing slides should carry one short title, one visual/flow, and
  two to four labels. Avoid slash-joined catch-all lines and explanatory
  paragraphs.
- Write labels as concrete nouns, verbs, numbers, or confirmation fields.
  Remove sentences that only promise improvement, integration, or future value.
- Use numbers with units whenever possible.
- For warehouse/rack projects, include aisle width, load, clear height, pallet count, and equipment constraints when known.
- If a fact is uncertain, mark it as an assumption instead of presenting it as confirmed.
- For customer-facing TWS business development decks, do not include internal
  status terms such as `lead_id`, `source_row`, `人工審核`, `資料缺口`, or `草稿`.
