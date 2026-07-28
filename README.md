# TWS AI Work Skills

Codex skills for TWS customer proposals and editable presentation production.

## Included skills

- `tws-customer-proposal-pipeline`: customer research, proposal thesis, TWS
  service mapping, and slide logic.
- `nokiy-presentation-generator`: editable PPTX production, TWS layout rules,
  and mechanical QA.
- `nokiy-deck-orchestrator`: source, copy, visual, build, and QA coordination
  for multi-file presentation work.

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

請檢查每個 SKILL.md、資料夾結構與相依技能。若已有同名技能，先比較版本，
不要直接覆寫。完成後回報安裝結果。
```

Restart ChatGPT after installation so the skills are available in new tasks.

## Local configuration

Edit `skills/nokiy-presentation-generator/references/assets-manifest.md` after
installation. Replace `<company-data-root>`, `<project-root>`, `<output-root>`,
and `<presenton-root>` with paths available on that computer.

## Dependencies

The complete deck orchestration flow may also use installed Humanizer, Codex
PPT, and PDF skills. Codex should report missing dependencies before starting a
full orchestration task.

## Version

Initial public release: `2026.07.28`.
