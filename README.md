# TWS AI Work Skills

Codex skills for TWS customer proposals, editable presentation production, and Taiwan-local copy review.

## Included skills

- `nokiy-deck-orchestrator`: authoritative natural-language entry point,
  customer/case routing, source control, build, QA, publishing, and readback.
- `tws-customer-proposal-pipeline`: customer research, proposal thesis, TWS
  service mapping, and slide logic.
- `nokiy-presentation-generator`: editable PPTX production, TWS layout rules,
  verified asset selection, visual QA, and mechanical QA.
- `humanizer-zh-tw`: Taiwan-local copy review with TWS bans on formulaic AI
  sentence patterns.
- `codex-ppt`: visual sample, full-size rendered-slide inspection, repair
  loops, and blocking visual acceptance evidence.

CAD drafting, rack layout, and engineering drawing skills are not included in
this release.

## Install with Codex

Paste this into a new Codex task:

```text
請使用內建的 skill-installer，從 https://github.com/nokiyliao/tws-ai-work-skills
安裝以下技能到 ~/.codex/skills/：
- skills/tws-customer-proposal-pipeline
- skills/nokiy-presentation-generator
- skills/nokiy-deck-orchestrator
- skills/humanizer-zh-tw
- skills/codex-ppt

請檢查每個 SKILL.md、資料夾結構與相依技能。若已有同名技能，比較版本並保留
較新的內容；發現衝突時向我說明。完成後回報安裝結果。
```

Restart ChatGPT after installation so the skills are available in new tasks.

## Local configuration

Edit `skills/nokiy-presentation-generator/references/assets-manifest.md` after
installation. Replace `<company-data-root>`, `<project-root>`, `<output-root>`,
and `<presenton-root>` with paths available on that computer.

## Dependencies

The complete deck orchestration flow also uses the installed PDF and
Presentations capabilities. Codex should report missing dependencies before
starting a full orchestration task.

## Version

Current optimized release: `2026.08.05`.
