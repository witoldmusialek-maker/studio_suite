# T-005 — Fiche Correction / Void / Status Flow

Status: accepted
Project Objective: AIOS-OBJ-SS-005 — Legacy CAISSE Fiche Correction / Void / Status Flow
Authority: Sponsor
Branch: `feature/legacy-caisse-flow`

## Goal

Make Legacy CAISSE corrections safe after T-003/T-004 established:

```text
fiche create/list → cash session open/close → daily summary
```

This ticket should answer:

```text
Can a salon safely void/correct a mistaken fiche without silently corrupting the daily cash summary or a closed cash day?
```

## Scope

Implement the smallest useful slice covering:

1. Safe void/status flow for an existing Legacy CAISSE fiche/sale.
2. Consistent payment status behavior when a fiche is voided.
3. Daily summary exclusion for voided/non-counting payments.
4. Protection against ordinary correction/void after the cash session is closed.
5. Predictable behavior for duplicate void attempts.
6. Minimal UI action from the existing fiche list, without redesign.
7. Tenant/salon/module guard preservation.

Prefer extending existing `void_fiche`, `Sale`, `Payment`, `CashierCashSession`, `LegacyCaissePage`, and tests over creating parallel correction concepts.

## Candidate Scope Paths

Primary candidate areas:

- `studio_suite/backend/app/api/v1/legacy_caisse.py`
- `studio_suite/backend/app/schemas/legacy_caisse.py`
- `studio_suite/backend/tests/`
- `studio_suite/frontend/src/pages/LegacyCaissePage.tsx`
- `studio_suite/docs/handoffs/`
- `studio_suite/docs/postmortems/`

## Forbidden / Guarded Paths

Do not modify unless explicitly justified in handoff:

- `studio_suite/backend/app/public_main.py`
- `studio_suite/backend/app/api/v1/public_*`
- `studio_suite/frontend_public/`
- deployment scripts
- nginx/gateway configs
- secrets/env files
- unrelated reporting, inventory, SMS, auth, or public booking modules

## Acceptance Criteria

1. Existing tenant/salon-scoped fiche can be voided by an authorized operational user.
2. Associated payment records become non-counting for daily summary.
3. Voided fiche/payment is excluded from the T-004 daily summary totals.
4. Duplicate void is either idempotent or returns a predictable conflict; chosen behavior is tested and documented.
5. Ordinary void/correction after cash-session close is blocked or requires an explicit correction path; chosen behavior is tested and documented.
6. Unsupported status transitions are rejected with clear 4xx behavior and no partial persistence.
7. Existing T-003 create/list behavior remains compatible.
8. Existing T-004 cash-session lifecycle/summary behavior remains compatible.
9. Legacy CAISSE UI exposes a minimal void/correction action from fiche list and refreshes list/summary afterward.
10. Tenant/salon/module guards remain enforced.
11. Public booking surface remains untouched and does not expose Legacy CAISSE.
12. Tests/checks pass and are recorded.

## Required Checks

Run and report:

```bash
git status --short
cd studio_suite/backend && .venv/bin/python -m pytest tests/test_legacy_caisse_minimal_flow.py tests/test_legacy_caisse_cash_session.py tests/test_legacy_caisse_fiche_correction.py -q
cd studio_suite/backend && .venv/bin/python -m compileall app
cd studio_suite/frontend && npm run build -- --outDir /tmp/studio-suite-vite-build --emptyOutDir
```

Runtime health when environment is available:

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://192.168.50.20:8003/health
curl -s -o /dev/null -w '%{http_code}\n' http://192.168.50.20:8004/health
curl -s -o /dev/null -w '%{http_code}\n' https://dev2.witold.ovh/health
```

## Deliverables

- Code changes for safe fiche void/status flow.
- Targeted backend tests for correction/void and daily summary exclusion.
- Minimal frontend action from fiche list.
- Handoff under `studio_suite/docs/handoffs/`.
- Postmortem under `studio_suite/docs/postmortems/` if implementation is delegated.

## Out of Scope

- full WinDev/Bureau reconstruction;
- WDD/FIC/NDX runtime checks;
- CAISSE-to-Bureau transfer;
- fiscal printing;
- receipt printing;
- full audit/accounting correction journal;
- exploitation reports;
- production deployment;
- merge to `master`;
- branch-policy decision;
- assigning Deployment Authority.
