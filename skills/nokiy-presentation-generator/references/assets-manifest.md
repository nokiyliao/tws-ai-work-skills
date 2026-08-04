# Assets Manifest (Canonical Paths)

All absolute paths used by the TWS deck skills live here. Other files must
reference this manifest instead of hard-coding paths, so a move only requires
editing this file.

## Contents

- TWS service-scope assets
- Master direction documents
- Logos and product source decks
- Generated-image storage
- Output locations
- Presenton local platform

If a path is missing, search for equivalents with `find` under:

- `/Users/nokiy/Desktop/🏢公司資料`
- `/Users/nokiy/Desktop/📋工作專案/新廠清單`

## TWS Service-Scope Asset Set (current authority: v0.8)

Base folder:
`/Users/nokiy/Desktop/📋工作專案/新廠清單/04_簡報與文件_Docs/陌生開發提案/demo_統流開發_TWS客戶版/tws_scope_assets/`

- Authoritative TWS full-service global image (default for every complete
  service-scope or integrated-logistics overview):
  `TWS_service_scope_authoritative_global_v0.8.png`
- This user-approved v0.8 image is the global visual authority. Use it before
  the v0.7 scene whenever the slide represents TWS's complete solution range.
  Do not regenerate, reinterpret, or silently substitute another overview.
- Shared new-factory visual catalog:
  `shared_factory_visuals/catalog.json`
- Reusable material-flow illustration:
  `shared_factory_visuals/TWS_shared_new_factory_material_flow_v1.png`

- Editable overlay master (slide 1 = customer overlay, slide 2 = full-coverage
  overlay, slide 3 = no-text base):
  `TWS_service_scope_editable_overlay_master_v0.7.pptx`
- Clean no-text 4K background:
  `TWS_service_scope_no_text_image2_v0.7_4K_clean.png`
- Overlay labels JSON:
  `TWS_service_scope_editable_overlay_master_v0.7_labels.json`
- PDF preview: `TWS_service_scope_editable_overlay_master_v0.7.pdf`

Older versions (v0.2–v0.7) remain in the same folder for reference and editable
overlay use; do not use them as the default full-range overview.

Keep the background as raster; labels, leader lines, brand names, and promise
boundaries must stay editable native PPTX objects (except for explicitly
requested PDF previews).

## Master Direction Documents

Current authoritative direction:
`/Users/nokiy/Desktop/📋工作專案/新廠清單/04_簡報與文件_Docs/陌生開發提案/demo_統流開發_TWS客戶版/TWS_客戶開發簡報權威母版_v0.7.md`

Older `_v0.x.md` versions are in the same folder; consult only if the user asks
about history.

## Logos

- TWS transparent logo folder:
  `/Users/nokiy/Desktop/🏢公司資料/其他檔案/Logo/TWS/TWS_NEW_LOGO_20200915`
- Brand material folder: `/Users/nokiy/Desktop/品牌素材/`

Logo rules: use transparent or official logo assets whenever available. Do not
use Image 2.0 to recreate logos. Place logos with contain/no-crop helpers such
as `add_logo()`; never crop, stretch, mask inside decorative circles, or merge
them into generated backgrounds when the user may need manual adjustment.

## Product Source Decks

- Common product source deck:
  `/Users/nokiy/Desktop/🏢公司資料/簡報資料/2025年/奔騰物流-自動化產品介紹Nokiy.pptx`
- Product/spec folders:
  `/Users/nokiy/Desktop/🏢公司資料/工作文件/產品與規格資料/01..08_*` (奔騰簡介,
  Modula, AMR/洗地機, 堆高機, 梭車, 料架與地坪, 碼頭月台, WMS 軟體)

## Generated Images

- Image 2.0 outputs land in `$CODEX_HOME/generated_images/<thread-id>/`
  (`/Users/nokiy/.codex/generated_images/<thread-id>/`).
- Always copy the chosen image into the customer deck `assets/` folder before
  referencing it in a build script.
- For new-factory decks, generate only the customer-specific cover by default.
  All interior workflow and service-scope pages must query the shared visual
  catalog first. Generate a new interior visual only after the catalog has no
  suitable asset and the gap is recorded in the build note.
- Missing required library assets are blocking errors. Never silently replace
  them with a photo, an older version, or an unrelated generated image.
- Record final generated/user/official images in `assets/registry.json` using
  `/Users/nokiy/.codex/skills/nokiy-presentation-generator/data/asset_registry.schema.json`.
- Allowed final uses: de-identified cover/chapter backgrounds, workflow or
  WMS/WCS concept illustrations, and non-product scenario visuals. Not allowed
  as logo, product proof, equipment-selection image, specific model exterior,
  or real-site evidence unless the user explicitly approves that image.

## Output Locations

- Scratch workspace (all decks):
  `/Users/nokiy/Documents/Playground/outputs/<timestamp>/presentations/<deck-slug>/`
- Final customer proposal deliverables:
  `/Users/nokiy/Desktop/📋工作專案/新廠清單/04_簡報與文件_Docs/陌生開發提案/<客戶名>_TWS客戶版/`
- Final filename patterns (pick the one matching the deck purpose; avoid
  `白皮書` for customer proposals and never `output.pptx`):
  - `<客戶名>_TWS智慧物流自動化導入交流提案_<YYYYMMDD>.pptx`
  - `<客戶名>_TWS三廠區倉儲物流改善提案_客戶決策版_<YYYYMMDD>.pptx`
  - `<客戶名>_TWS倉儲物流改善建議書_<YYYYMMDD>.pptx`
  - `<客戶名>_TWS設備選型與導入建議_<YYYYMMDD>.pptx`

## Presenton Local Platform (only when the user asks for the platform)

Checkout: `/Users/nokiy/Documents/Playground/presenton-local`
(FastAPI venv in `servers/fastapi/.venv`, Next.js deps installed, no Docker,
prefer the Web dev route over Electron.)

```bash
cd /Users/nokiy/Documents/Playground/presenton-local/servers/fastapi
PATH="$HOME/.local/bin:$PATH" APP_DATA_DIRECTORY=/Users/nokiy/Documents/Playground/presenton-local/app_data \
  CAN_CHANGE_KEYS=true DISABLE_ANONYMOUS_TRACKING=true \
  uv run python server.py --port 5000
```

```bash
cd /Users/nokiy/Documents/Playground/presenton-local/servers/nextjs
NEXT_PUBLIC_FAST_API=http://127.0.0.1:5000 FAST_API_INTERNAL_URL=http://127.0.0.1:5000 \
  npm run dev -- --port 3000
```

Open `http://localhost:3000?fastapiUrl=http://127.0.0.1:5000`.
