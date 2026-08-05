# Administrator Asset Maintenance

This document is not part of the learner workflow. Company learners use the
remote read-only asset service and natural-language deck requests only.

For an administrator maintaining the source library locally:

```bash
python scripts/preflight.py --workflow tws-new-factory \
  --asset-mode local --asset-library <asset-library-root>
```

The root must contain `catalog.json`, `select_assets.py`, and
`verify_assets.py`. Never commit that root, its absolute path, Cloudflare
Tunnel credentials, or any unrelated local path to this repository.

The learner Skill bundles only the public Tunnel base URL and catalog digest
pin. Administrators may override them through managed environment or device
configuration:

- `TWS_ASSET_LIBRARY_BASE_URL`
- `TWS_ASSET_LIBRARY_CATALOG_SHA256`
No learner token or additional login is required. Keep the origin bound to
loopback, expose only the catalog service through Tunnel ingress, and update
the catalog pin only after the new catalog and every referenced asset pass the
administrator verifier.
