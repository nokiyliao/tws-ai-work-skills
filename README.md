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
較新的內容；發現衝突時向我說明。

安裝後，請執行 nokiy-deck-orchestrator/scripts/bootstrap_learner.py（不要要求我輸入
素材庫路徑、hostname、token 或額外登入），自動驗證公司發布的唯讀素材服務。
接著執行 tws-new-factory 的 remote preflight；只有 bootstrap 與 preflight 都 PASS
才回報安裝完成，否則請 fail closed 並指出缺少的環境元件。
```

Restart ChatGPT after installation so the skills are available in new tasks.

## Company learner experience

Learners paste one installation prompt, open a customer workspace, and
describe the customer and presentation need in natural language. They do not configure the
shared asset-library filesystem, selector, verifier, Cloudflare hostname, or
credentials. The bootstrap reads the bundled non-secret service URL and
catalog pin, verifies the protected catalog, and writes the local learner
configuration only after verification succeeds. The orchestrator then obtains
a controlled job-local snapshot, verifies its catalog and asset digests, and
passes it to presentation QA.

Company IT publishes the remote service URL and catalog pin in the bundled
learner environment. The public endpoint exposes only the read-only catalog API;
the origin filesystem remains loopback-only and is never exposed. See
`skills/nokiy-deck-orchestrator/references/administrator-asset-maintenance.md`.

## Dependencies

The complete deck orchestration flow also uses the installed PDF and
Presentations capabilities. Codex should report missing dependencies before
starting a full orchestration task.

## Version

Current optimized release: `2026.08.05.2`.
