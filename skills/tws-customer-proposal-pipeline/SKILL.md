---
name: tws-customer-proposal-pipeline
description: Decide WHAT a TWS/TWSC/奔騰物流 proposal deck for a NAMED target customer should say — research the company's public signals (news, expansion, ERP/MES/ESG), form an opportunity thesis, choose the engagement mode and slide logic, couple signals to TWS services (WMS/WCS, racks, Modula, AGV/AMR, Galaxis, dock, LionsBot), and enforce customer-facing copy discipline. Use when the user names a target customer and wants a proposal, cold-development deck, improvement proposal, or decision deck, especially with a news URL, company website, or reference deck. Delegates PPTX construction and styling to nokiy-presentation-generator.
---

# TWS Customer Proposal Pipeline

Own the customer thesis, proposal structure, source discipline, and TWS service
coupling. File construction, styling, layout library, and the mechanical QA
script belong to `nokiy-presentation-generator` — when both skills are active,
this one decides business logic and authority order; that one builds files.

## Required References

Read only the relevant file(s):

- `references/source-intelligence.md` — research, verification, source notes.
- `references/tws-service-coupling.md` — mapping customer signals to TWS
  services and slide logic.
- `references/deck-production-qa.md` — production handoff, output paths, QA
  execution, failure handling.
- Customer-facing copy method:
  `~/.codex/skills/nokiy-presentation-generator/references/customer-copy.md`
  — use before writing visible slide copy.
- Governance (authority order, deletion rule, locked assets, hero images, copy
  and numeric discipline, QA gates) is canonical in
  `~/.codex/skills/nokiy-presentation-generator/references/shared-governance.md`
  — follow it for every customer-facing deck.

## Workflow

### 1. Classify The Engagement Mode

Infer target company, audience, and deliverable from the prompt; only ask when
genuinely ambiguous. Modes:

- `Cold development`: customer may not know TWS — concise signal analysis, TWS
  role, service scope, low-pressure meeting request.
- `Existing-customer improvement proposal`: minimal background — lead with pain
  points, improvement goals, recommended equipment/process, confirmation items,
  next actions.
- `Customer decision deck`: problem-to-solution logic, measurable tracking
  items, staged deployment, risk/condition boundaries.
- `Internal planning`: only when explicitly requested.
- `Revision of an existing deck`: preserve page count, layout, and naming;
  apply comments and Markdown specs literally before adding ideas. Revision
  scope rules: `shared-governance.md`.

### 2. Build The Customer Intelligence Base

Browse for current information unless told not to
(`references/source-intelligence.md`). Priority: user URL → official company /
investor / ESG pages → credible industry news → user-supplied local files.
Extract only proposal-relevant signals; record exact source dates; never invent
metrics. For existing-customer work, keep public background minimal.

### 3. Create The TWS Opportunity Thesis

Turn facts into a business-language hypothesis: what the customer is changing,
why logistics matters now, which TWS services to discuss first, what to confirm
in the first meeting (`references/tws-service-coupling.md`). Position TWS as an
integrated warehouse/logistics partner, never a single-equipment vendor.

### 4. Design The Deck

Length follows the mode: 8–10 slides for cold development, ~12 for improvement
proposals, 12–16 for full proposals/decision decks; trim filler. Recommended
full-proposal spine:

1. Customer-specific title.  2. Public signals / why now.  3. Operating
thesis.  4. Pain-point translation.  5. TWS service map.  6. System
architecture (ERP/MES → WMS/WCS → equipment).  7. WMS/WCS foundation.
8. Storage module.  9. Line-side / AGV/AMR module.  10. New factory / old
site / dock / ESG module as applicable.  11. Traceability and tracking frame.
12. Roadmap.  13. Meeting inputs.  14. Closing CTA.

Detailed structures per mode (8–10 slide cold development, 12-slide
improvement) live in
`~/.codex/skills/nokiy-presentation-generator/references/tws-business-development-deck.md`.

User-provided Markdown specs are contracts; deletion is authoritative
(`shared-governance.md`).

### 4A. Select Reusable Asset Candidates

After the slide logic is known, create a deck requirements JSON with
`deck_mode`, intended `purposes`, proposal-specific `focus_tags`, and permitted
`evidence_levels`. Use it together with the matching customer profile to call
the verified asset-library selector and write a thread/deck-specific
`<scratch>/asset-selection.json`:

```bash
python3 ~/.codex/skills/nokiy-deck-orchestrator/scripts/remote_asset_library.py \
  --profile <scratch>/customer-profile.json \
  --requirements <scratch>/deck-requirements.json \
  --stage <scratch>/assets/remote-library \
  --limit 6
```

The installed Skill carries the company-published service URL and catalog
SHA-256 pin. Learners never enter a filesystem path, hostname, token, or
additional login during a presentation task.
Do not hard-code asset files into this skill. The output is a candidate list,
not a slide-placement plan; retain that decision for deck design. Keep
`official` for product evidence and `concept` for de-identified scenarios.
`customer_only` is retained for selection and audit; it is not an internal
asset-service access-control mechanism.

### 5. Copy Discipline

Write to the customer, not about the deck. Canonical rules and the
machine-readable term lists:
`shared-governance.md` + `nokiy-presentation-generator/data/banned_terms.json`.
Visible slides default to a short title, one visual/flow, and two to four
labels. Keep rationale, caveats, and the speaking script out of the slide;
put them in speaker notes or the private build note. Use the generator's
`references/customer-copy.md` before writing the handoff.
Quick anchors: prefer `確認項目`, `確認條件`, `追蹤項目`, `本次範圍`,
`下一步`, `狀態回報`; no unsupported business numbers —
write missing figures as confirmation items.

### 6. Build And Validate

Delegate construction to `nokiy-presentation-generator` (its `tws_pptx.py`
library and style defaults). Then:

- Run its `scripts/qa_check.py` with the right mode and slide count.
- Pass the job-local materialized snapshot as `--asset-library` together with
  `--asset-selection-manifest`. This digest/role gate must pass before use.
- Apply the QA level from `shared-governance.md` (Light / Standard / Full +
  Decision Consistency for decision and improvement decks).
- Hero/cover image QA and Image 2.0 style rules are blocking for
  customer-facing decks (`shared-governance.md`). When generated conceptual
  visuals are needed, default to low-realism flat business illustrations unless
  the user explicitly asks for photorealism or official/product proof imagery.
- Execution details, render commands, and failure handling:
  `references/deck-production-qa.md`.

### 7. Handoff

Final deliverable goes to the customer proposal folder with a purpose-matched
filename — paths and patterns in
`nokiy-presentation-generator/references/assets-manifest.md`. If Drive
upload/import is unavailable, use the local Google Drive Desktop sync folder
and verify with Drive search. In the final response give the absolute file
link, slide count, QA level completed, major sources, and any handoff
limitation. Keep it concise.
