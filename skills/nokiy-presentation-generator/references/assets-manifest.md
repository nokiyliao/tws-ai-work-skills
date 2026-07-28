# Assets Manifest (Portable Configuration)

Configure the paths in this file for each computer. Other files should refer to
this manifest instead of hard-coding local paths.

## Contents

- TWS service-scope assets
- Master direction documents
- Logos and product source decks
- Generated-image storage
- Output locations
- Presenton local platform

Choose three local roots before the first run:

- `<company-data-root>`: official company, product, logo, and brand files.
- `<project-root>`: active customer or business-development projects.
- `<output-root>`: temporary renders, QA files, and final deliverables.

## TWS Service-Scope Asset Set (current: v0.7)

Base folder: `<company-data-root>/presentation-assets/tws-scope/`

- Editable overlay master (slide 1 = customer overlay, slide 2 = full-coverage
  overlay, slide 3 = no-text base):
  `TWS_service_scope_editable_overlay_master_v0.7.pptx`
- Clean no-text 4K background:
  `TWS_service_scope_no_text_image2_v0.7_4K_clean.png`
- Overlay labels JSON:
  `TWS_service_scope_editable_overlay_master_v0.7_labels.json`
- PDF preview: `TWS_service_scope_editable_overlay_master_v0.7.pdf`

Older versions (v0.2–v0.6) remain in the same folder for reference only; do not
use them by default.

Keep the background as raster; labels, leader lines, brand names, and promise
boundaries must stay editable native PPTX objects (except for explicitly
requested PDF previews).

## Master Direction Documents

Current authoritative direction:
`<company-data-root>/presentation-guides/TWS_customer_deck_master.md`

Older `_v0.x.md` versions are in the same folder; consult only if the user asks
about history.

## Logos

- TWS transparent logo folder: `<company-data-root>/brand/logos/TWS/`
- Brand material folder: `<company-data-root>/brand/`

Logo rules: use transparent or official logo assets whenever available. Do not
use Image 2.0 to recreate logos. Place logos with contain/no-crop helpers such
as `add_logo()`; never crop, stretch, mask inside decorative circles, or merge
them into generated backgrounds when the user may need manual adjustment.

## Product Source Decks

- Common product source deck:
  `<company-data-root>/product-decks/TWS_product_overview.pptx`
- Product/spec folders: `<company-data-root>/products/` (奔騰簡介, Modula,
  AMR/洗地機, 堆高機, 梭車, 料架與地坪, 碼頭月台, WMS 軟體)

## Generated Images

- Image 2.0 outputs land in `$CODEX_HOME/generated_images/<thread-id>/`
  (`~/.codex/generated_images/<thread-id>/`).
- Always copy the chosen image into the customer deck `assets/` folder before
  referencing it in a build script.
- Record final generated/user/official images in `assets/registry.json` using
  `~/.codex/skills/nokiy-presentation-generator/data/asset_registry.schema.json`.
- Allowed final uses: de-identified cover/chapter backgrounds, workflow or
  WMS/WCS concept illustrations, and non-product scenario visuals. Not allowed
  as logo, product proof, equipment-selection image, specific model exterior,
  or real-site evidence unless the user explicitly approves that image.

## Output Locations

- Scratch workspace: `<output-root>/<timestamp>/presentations/<deck-slug>/`
- Final customer proposal deliverables:
  `<project-root>/<客戶名>/deliverables/`
- Final filename patterns (pick the one matching the deck purpose; avoid
  `白皮書` for customer proposals and never `output.pptx`):
  - `<客戶名>_TWS智慧物流自動化導入交流提案_<YYYYMMDD>.pptx`
  - `<客戶名>_TWS三廠區倉儲物流改善提案_客戶決策版_<YYYYMMDD>.pptx`
  - `<客戶名>_TWS倉儲物流改善建議書_<YYYYMMDD>.pptx`
  - `<客戶名>_TWS設備選型與導入建議_<YYYYMMDD>.pptx`

## Presenton Local Platform (only when the user asks for the platform)

Checkout: `<presenton-root>`
(FastAPI venv in `servers/fastapi/.venv`, Next.js deps installed, no Docker,
prefer the Web dev route over Electron.)

```bash
cd <presenton-root>/servers/fastapi
PATH="$HOME/.local/bin:$PATH" APP_DATA_DIRECTORY=<presenton-root>/app_data \
  CAN_CHANGE_KEYS=true DISABLE_ANONYMOUS_TRACKING=true \
  uv run python server.py --port 5000
```

```bash
cd <presenton-root>/servers/nextjs
NEXT_PUBLIC_FAST_API=http://127.0.0.1:5000 FAST_API_INTERNAL_URL=http://127.0.0.1:5000 \
  npm run dev -- --port 3000
```

Open `http://localhost:3000?fastapiUrl=http://127.0.0.1:5000`.
