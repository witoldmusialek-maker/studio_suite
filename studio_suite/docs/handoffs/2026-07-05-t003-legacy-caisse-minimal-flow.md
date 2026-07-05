# Handoff — T-003 Legacy CAISSE Minimal Flow

Date: 2026-07-05
Status: ready-for-review
Objective: AIOS-OBJ-SS-003 — Legacy CAISSE Minimal Flow
Branch: feature/legacy-caisse-flow

## Scope delivered

Implemented the bounded backend hardening needed for the already-present minimal Legacy CAISSE cashier flow:

- creation of a minimal cashier fiche/sale remains available through `POST /api/v1/legacy/caisse/fiches`;
- current-month fiche listing remains available through `GET /api/v1/legacy/caisse/fiches`;
- sale lines persist legacy worker/service code snapshots, totals, discount, payment, allocations, and payment lines;
- added automated tests proving create/list behavior and new guard behavior.

Frontend operational CAISSE page already contained the minimal entry/payment/list path and was verified by production build. No public booking files were changed.

## Files changed

- `studio_suite/backend/app/api/v1/legacy_caisse.py`
  - added pre-persistence fiche line validation;
  - rejects staff not assigned/member of the target salon;
  - rejects inactive/missing service lines;
  - validates product availability through active salon product link;
  - validates active bundle presence for bundle lines.
- `studio_suite/backend/tests/test_legacy_caisse_minimal_flow.py`
  - added focused tests for minimal create/list flow;
  - added guard test for staff from another salon;
  - added guard test for inactive service.
- `studio_suite/docs/flags/2026-07-05-t003-legacy-caisse-minimal-flow.json`
  - status moved to `ready-for-review`, execution package marked committed.

## Validation evidence

```text
backend targeted pytest: PASS
Command: cd studio_suite/backend && .venv/bin/python -m pytest tests/test_legacy_caisse_minimal_flow.py -q
Result: 3 passed, 7 warnings

backend compileall: PASS
Command: cd studio_suite/backend && .venv/bin/python -m compileall app
Result: completed successfully

frontend build: PASS
Command: cd studio_suite/frontend && npm run build -- --outDir /tmp/studio-suite-vite-build --emptyOutDir
Result: ✓ built in 26.46s

runtime health: PASS
http://192.168.50.20:8003/health -> 200
http://192.168.50.20:8004/health -> 200
https://dev2.witold.ovh/health -> 200
```

Warnings observed:

- existing SQLAlchemy `declarative_base()` deprecation warning;
- existing passlib `crypt` deprecation warning;
- existing Pydantic class-based config deprecation warnings;
- existing Vite CJS API deprecation and chunk-size warnings.

No warning blocked the delivery checks.

## Guard evidence

- Tenant/salon boundary: `_ensure_access` still validates target salon belongs to current user's tenant; new line validation rejects staff not attached to the fiche salon.
- Module/license boundary: `legacy_caisse.router` remains registered with `Depends(require_module_legacy_caisse)` in `app/api/v1/__init__.py`; no change weakened it.
- Public/private separation: no `public_*`, `public_main.py`, or public frontend files were changed.
- No secrets were added.
- No deploy, production operation, or merge to `master` was performed.

## Known limitations / deferred scope

- This is the minimal backend-verified cashier flow; no full WinDev/Bureau reconstruction.
- No WDD/FIC/NDX runtime checks.
- No CAISSE-to-Bureau transfer.
- No exploitation reports or file database synchronization.
- Authenticated browser smoke was not run because approved credentials/TOTP flow is outside the committed evidence package; runtime health and build were verified.

## PM review recommendation

Ready for PM review. If accepted, Sponsor may accept T-003 as the first bounded Legacy CAISSE delivery slice. Deployment and merge-to-master remain separate authority decisions.
