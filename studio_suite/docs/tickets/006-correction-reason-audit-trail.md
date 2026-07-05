# T-006 — Correction Reason / Audit Trail

Status: accepted
Project Objective: AIOS-OBJ-SS-006 — Legacy CAISSE Correction Reason / Audit Trail
Authority: Sponsor
Branch: `feature/legacy-caisse-flow`

## Goal

Make Legacy CAISSE void/correction actions auditable enough for controlled pilot use.

After T-005, voiding is safe. T-006 should answer:

```text
Who voided/corrected this fiche, when, and why?
```

## Scope

Implement the smallest useful audit trail covering:

1. Reason capture for void/correction action.
2. Persistence of correction/audit metadata linked to sale/fiche.
3. Minimal backend read path for audit history.
4. Minimal Legacy CAISSE UI reason flow and history display.
5. Preservation of T-003/T-004/T-005 behavior.

Prefer a small explicit model/table over overloading unrelated fields if no suitable existing audit model exists.

## Candidate Scope Paths

Primary candidate areas:

- `studio_suite/backend/app/models/salon_core.py`
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

1. Void/correction action records a human-readable reason linked to sale/fiche.
2. Audit record includes tenant id, salon id, sale id, actor/user id, action type, reason, timestamp, previous status, and new status.
3. Backend exposes a minimal tenant/salon-scoped read path for correction/audit history for a fiche/sale.
4. Legacy CAISSE UI uses an explicit reason flow instead of bare click-to-void.
5. UI refreshes fiche list, daily summary, and audit/history state after successful action.
6. Closed-day protection from T-005 remains intact and failed closed-day void does not create a success audit record.
7. Voided payments remain excluded from T-004 daily summary totals.
8. Existing T-003 create/list behavior remains compatible.
9. Existing T-004 cash-session lifecycle/summary behavior remains compatible.
10. Existing T-005 duplicate void and closed-day behavior remains compatible.
11. Tenant/salon/module guards remain enforced.
12. Public booking surface remains untouched and does not expose Legacy CAISSE.
13. Tests/checks pass and are recorded.

## Required Checks

Run and report:

```bash
git status --short
cd studio_suite/backend && .venv/bin/python -m pytest tests/test_legacy_caisse_minimal_flow.py tests/test_legacy_caisse_cash_session.py tests/test_legacy_caisse_fiche_correction.py tests/test_legacy_caisse_correction_audit.py -q
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

- Minimal audit model/schema and API changes for correction reason/history.
- Targeted backend tests for reason/audit and regression behavior.
- Minimal frontend reason flow/history display.
- Handoff under `studio_suite/docs/handoffs/`.
- Postmortem under `studio_suite/docs/postmortems/` if implementation is delegated.

## Out of Scope

- full audit/accounting correction journal;
- fiscal/invoice correction semantics;
- fiscal printing;
- receipt printing;
- exploitation reports;
- CAISSE-to-Bureau transfer;
- WDD/FIC/NDX runtime checks;
- production deployment;
- merge to `master`;
- branch-policy decision;
- assigning Deployment Authority.
