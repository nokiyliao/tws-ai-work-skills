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

安裝 Skill 後，請立刻執行跨平台 runtime bootstrap（不要要求我輸入素材庫路徑、
hostname、token、Access 登入或本機素材路徑）：

若缺少 Python 3.10+ 或 uv，請先由 Codex 安裝到使用者目錄；不得使用系統管理員
權限，也不得污染全域 site-packages。

python ~/.codex/skills/nokiy-deck-orchestrator/scripts/runtime_bootstrap.py install

此指令會：
1. 偵測 Windows/macOS、Python、uv
2. 在使用者可控的隔離位置建立 runtime（預設 ~/.codex/runtimes/tws-ai）
3. 依 runtime/requirements.lock 安裝簡報套件與 RapidOCR/ONNX Runtime（Windows 另含 pywin32）
4. 跑最小 smoke：可開啟 PPTX、渲染/產生一頁 PNG、驗證 OCR engine
5. 執行遠端素材 bootstrap_learner 與 tws-new-factory remote preflight

Python 與 uv 可由 Codex 安裝到使用者目錄；不要污染全域 site-packages。
Microsoft Office / LibreOffice 等系統應用不得偽稱已自動安裝；
若缺少，typed fail closed 並回報精確 blocker（可能需要系統管理員或 GUI 安裝）。

只有 runtime_bootstrap 與 preflight 都 PASS 才回報安裝完成，否則 fail closed。
```

Restart ChatGPT after installation so the skills are available in new tasks.

## Install the learner plugins

The learner plugin package installs or enables 13 course plugins that do not
require an external account login. It explicitly excludes Google Drive, Gmail,
Outlook Email, GitHub, Cloudflare, and the three private UTM/test-workspace
plugins. It contains identifiers and setup instructions only;
credentials, OAuth tokens, plugin caches, and personal configuration are never
included.

Open [`learner-setup/INSTALL_PLUGINS_PROMPT.md`](learner-setup/INSTALL_PLUGINS_PROMPT.md),
copy the prompt into a new Codex task, and follow any restart or local permission
instructions Codex reports. The authoritative machine-readable list is
[`learner-setup/plugins.manifest.json`](learner-setup/plugins.manifest.json).

## Presentation routing

`nokiy-deck-orchestrator` is the only user-facing entry point for creating,
revising, validating, delivering, or publishing a presentation. The proposal
pipeline, editable generator, and Codex-PPT are internal phases and require a
passing `deck_pipeline_state.py route` guard. The routing contract is declared
in `manifest.json` and validated by the repository test suite.

TWS company, capability, product, and teaching decks use the `tws-company`
workflow; named-customer and new-factory proposals use `tws-new-factory`. Both
routes require the remote selection manifest, digest verification, a per-slide
visual plan, and post-build proof that planned images are embedded on the
declared slides. The Markdown converter is limited to non-TWS internal drafts.

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

### Isolated Python runtime

Deck production Python packages install into an isolated runtime, never the
global interpreter:

- Default path: `~/.codex/runtimes/tws-ai` (override with `TWS_AI_RUNTIME_HOME`)
- Declaration: `skills/nokiy-deck-orchestrator/runtime/requirements.txt`
- Lockfile: `skills/nokiy-deck-orchestrator/runtime/requirements.lock`
- Packages: `python-pptx`, `Pillow`, `PyMuPDF`, `RapidOCR`, `ONNX Runtime`, and Windows-only `pywin32`

Bootstrap and verify:

```bash
python skills/nokiy-deck-orchestrator/scripts/runtime_bootstrap.py install
python skills/nokiy-deck-orchestrator/scripts/runtime_bootstrap.py check
python skills/nokiy-deck-orchestrator/scripts/preflight.py --workflow tws-new-factory
```

### System applications (not auto-installed)

The complete deck flow also needs a PPTX renderer and OCR on the host:

- Renderer: Microsoft PowerPoint (Windows COM via pywin32) or LibreOffice (`soffice`)
- PDF rasterizer: Poppler `pdftoppm` and/or PyMuPDF in the isolated runtime
- OCR: isolated RapidOCR with ONNX Runtime; macOS Vision and Tesseract are optional preferred alternatives

Missing rendering tools remain blocking failures such as
`SYSTEM_RENDERER_MISSING`. OCR fails closed only when neither the isolated
RapidOCR engine nor a validated host engine is available.

## Version

Current optimized release: `2026.08.05.6`.
