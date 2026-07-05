# Handoff — T-005 Fiche Correction / Void / Status Flow

Date: 2026-07-05
Status: ready-for-review
Objective: AIOS-OBJ-SS-005 — Legacy CAISSE Fiche Correction / Void / Status Flow
Branch: feature/legacy-caisse-flow

## Scope delivered

Implemented the bounded Legacy CAISSE correction slice:

- existing fiche can be voided safely while the cash day is open;
- associated payment is moved to `void`, making it non-counting for T-004 daily summary;
- duplicate void is idempotent and returns `VOID`;
- ordinary void after cash-session close is blocked with `409`;
- Legacy CAISSE fiche list exposes a minimal click-to-void action and refreshes list/summary;
- T-003 create/list and T-004 cash-session/summary tests remain green.

## Files changed

- `studio_suite/backend/app/api/v1/legacy_caisse.py`
  - hardened `void_fiche` with idempotent duplicate behavior;
  - blocks ordinary void when the sale business date has a closed cash session;
  - keeps sale/payment void status consistent.
- `studio_suite/backend/tests/test_legacy_caisse_fiche_correction.py`
  - added tests for void, summary exclusion, duplicate void, and closed-day protection.
- `studio_suite/frontend/src/pages/LegacyCaissePage.tsx`
  - added minimal fiche-list void action;
  - refreshes fiches and daily summary after void.
- `studio_suite/docs/flags/2026-07-05-t005-fiche-correction-void-status-flow.json`
  - moved to `ready-for-review` with check results.
- `studio_suite/docs/tickets/005-fiche-correction-void-status-flow.md`
  - moved to `ready-for-review`.

## Status-transition semantics

```text
COMPLETED/PENDING + void while day open -> Sale.status = VOID, Payment.status = void
VOID + void                         -> idempotent VOID response
COMPLETED/PENDING + void after close -> 409 conflict, no mutation
missing fiche                       -> 404
cross-salon/user without access      -> blocked by existing _ensure_access
```

## Daily summary exclusion

T-004 daily summary already counts only `Payment.status == "completed"`. T-005 sets associated payments to `void`, so voided fiches no longer contribute to:

- `service_gross`;
- `retail_gross`;
- `discount_total`;
- `payments_by_method`;
- `cash_payments`;
- `expected_cash`.

## Validation evidence

```text
backend targeted pytest: PASS
Command: cd studio_suite/backend && .venv/bin/python -m pytest tests/test_legacy_caisse_minimal_flow.py tests/test_legacy_caisse_cash_session.py tests/test_legacy_caisse_fiche_correction.py -q
Result: 8 passed, 7 warnings

backend compileall: PASS
Command: cd studio_suite/backend && .venv/bin/python -m compileall app
Result: completed successfully

frontend build: PASS
Command: cd studio_suite/frontend && npm run build -- --outDir /tmp/studio-suite-vite-build --emptyOutDir
Result: ✓ built in 25.67s

runtime health: PASS
http://192.168.50.20:8003/health -> 200
http://192.168.50.20:8004/health -> 200
https://dev2.witold.ovh/health -> 200
```

Warnings observed are existing non-blocking warnings:

- SQLAlchemy `declarative_base()` deprecation;
- passlib `crypt` deprecation;
- Pydantic class-based config deprecations;
- Vite CJS API deprecation and chunk-size warnings.

## Guard evidence

- Tenant/salon access still goes through `_ensure_access` for void operations.
- Closed cash day blocks ordinary void/correction.
- Daily summary excludes voided payments.
- `legacy_caisse.router` remains behind the `LEGACY_CAISSE` module dependency registered outside this file.
- No public booking files were changed.
- No deployment scripts, nginx configs, or secrets were changed.
- No production deployment or merge to `master` was performed.

## Known limitations / deferred scope

- No full correction journal/audit model was introduced.
- No explicit correction reason is persisted because the current model has no dedicated correction-reason field.
- UI action is intentionally minimal: click a fiche in the fiche list and confirm void.
- No fiscal printing, receipt printing, Bureau transfer, WDD/FIC/NDX checks, or file synchronization.

## PM review recommendation

Ready for PM review. If accepted, Sponsor may accept T-005 as the safe correction/void slice required before richer reports or deployment decisions.
