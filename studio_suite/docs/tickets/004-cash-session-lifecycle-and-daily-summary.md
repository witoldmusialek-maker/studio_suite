# T-004 — Cash Session Lifecycle and Daily Summary

Status: accepted
Project Objective: AIOS-OBJ-SS-004 — Legacy CAISSE Daily Cash Session
Authority: Sponsor
Branch: `feature/legacy-caisse-flow`

## Goal

Deliver a minimal day-cycle for Legacy CAISSE:

```text
open cash session → use cashier fiche flow → record expenses/presence → close cash session → review daily summary
```

This should make the accepted T-003 cashier fiche flow usable within a salon's daily cash operation.

## Scope

Implement the smallest useful slice covering:

1. Open cash session for tenant/salon/business date with opening cash.
2. Prevent duplicate session creation for the same tenant/salon/business date.
3. Close an open session with closing cash and close metadata where supported.
4. Protect closed sessions from ordinary silent overwrite/reopen.
5. Expose a minimal daily summary for the same tenant/salon/business date.
6. Show open/close/summary state in the existing Legacy CAISSE UI without redesign.
7. Preserve tenant isolation, salon access validation, and `LEGACY_CAISSE` module/license guard.

Prefer extending existing `CashierCashSession`, `CashierExpense`, `Sale`, `SaleLine`, `Payment`, `PaymentAllocation`, and existing Legacy CAISSE endpoints/components over creating parallel concepts.

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

1. Cash session can be opened for a tenant-scoped salon/date.
2. Duplicate cash session for same tenant/salon/date is blocked or idempotently handled without duplicates.
3. Open cash session can be closed with closing cash.
4. Closed session is protected from ordinary silent overwrite/reopen.
5. Daily summary returns at least:
   - opening cash;
   - service gross;
   - retail/product gross;
   - discount total;
   - payments by method;
   - cash payments;
   - expenses total;
   - expected cash;
   - closing cash;
   - cash difference.
6. Existing T-003 fiche create/list behavior remains compatible.
7. Tenant/salon/module guards remain enforced.
8. Public booking surface remains untouched and does not expose Legacy CAISSE.
9. Tests/checks pass and are recorded.

## Required Checks

Run and report:

```bash
git status --short
cd studio_suite/backend && .venv/bin/python -m pytest tests/test_legacy_caisse_minimal_flow.py tests/test_legacy_caisse_cash_session.py -q
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

- Code changes for cash session lifecycle and summary.
- Targeted backend tests for lifecycle and summary calculations.
- Frontend build verification.
- Handoff under `studio_suite/docs/handoffs/`.
- Postmortem under `studio_suite/docs/postmortems/` if implementation is delegated.

## Out of Scope

- full WinDev/Bureau reconstruction;
- WDD/FIC/NDX runtime checks;
- CAISSE-to-Bureau transfer;
- exploitation reports;
- fiscal printing;
- broad reporting rewrite;
- production deployment;
- merge to `master`;
- branch-policy decision;
- assigning Deployment Authority.
