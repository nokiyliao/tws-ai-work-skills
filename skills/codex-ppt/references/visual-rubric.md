# Visual Acceptance Rubric

Use every section on every customer-facing deck. A single blocking defect makes
the slide fail.

## Per-Slide Checks

1. **Role**: The page fulfills its approved outline role and communicates one
   primary decision point within three seconds.
2. **Hierarchy**: Title, subtitle, labels, numbers, notes, and source marks have
   a clear reading order without competing focal points.
3. **Composition**: Margins, alignment, grouping, spacing, and negative space
   are intentional. The page is neither crowded nor accidentally empty.
4. **Legibility**: Text is readable at presentation distance. No clipping,
   overflow, tiny type, weak contrast, or dense paragraph substitutes for a
   visual.
5. **Images**: Images are sharp, correctly cropped, undistorted, and relevant.
   Official logos and products preserve identity and aspect ratio.
6. **Generated media**: No fake text, logo, watermark, malformed equipment,
   repeated object, impossible geometry, or unexplained crop. Concept imagery
   never impersonates product or customer-site evidence.
7. **Diagrams**: Arrows connect intended objects, lines terminate cleanly,
   labels belong to the correct node, and the flow has no ambiguous direction.
8. **Leakage**: No prompt, placeholder, debug content, internal instruction,
   hidden-working artifact, or accidental page number is visible.

## Deck-Level Checks

- Palette, typography, icon/image treatment, margins, and grid remain coherent.
- Page layouts vary by role without becoming mechanically repetitive.
- Cover, section, workflow, comparison, architecture, proof, roadmap, and
  closing pages form a deliberate rhythm.
- Reused visuals retain the same crop, color treatment, and meaning.
- Revisions do not introduce drift on untouched slides.

## Report Contract

Write `visual_qa.json` with this shape:

```json
{
  "schema_version": "codex_ppt_visual_qa_v1",
  "deck": "final.pptx",
  "sample_status": "pass",
  "slides": [
    {
      "slide": 1,
      "verdict": "PASS",
      "findings": [],
      "render": "rendered/slide-01.png"
    }
  ],
  "repaired_slides": [],
  "deck_verdict": "PASS"
}
```

`sample_status` is `pass` or `skipped`; when skipped, include a nonempty
`sample_skip_reason`. Each failed iteration should remain in the build notes,
while the final JSON describes the final rendered set.
