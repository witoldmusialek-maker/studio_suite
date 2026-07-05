# Handoff — T-006 Correction Reason / Audit Trail

Date: 2026-07-05
Status: ready-for-review
Objective: AIOS-OBJ-SS-006 — Legacy CAISSE Correction Reason / Audit Trail
Branch: feature/legacy-caisse-flow

## Delivered

T-006 adds the smallest useful audit trail for Legacy CAISSE void/correction actions.

Implemented behavior:

- void requires a human-readable reason;
- void creates a correction audit record;
- audit record stores tenant, salon, sale, actor, action type, reason, previous status, new status, created_at;
- backend exposes fiche-level audit history;
- duplicate void remains idempotent and does not create a second success mutation;
- closed-day void remains blocked and does not create a success audit record;
- voided payments remain excluded from daily summary;
- frontend asks for a reason before void;
- frontend displays audit history after void or when clicking an already-voided fiche.

## Changed files

Backend:

- `studio_suite/backend/app/models/salon_core.py`
  - added `CashierCorrectionAudit`.
- `studio_suite/backend/app/schemas/legacy_caisse.py`
  - added `LegacyCaisseVoidWrite`;
  - added `LegacyCaisseCorrectionAuditRead`;
  - extended `LegacyCaisseVoidResponse` with optional `reason`.
- `studio_suite/backend/app/api/v1/legacy_caisse.py`
  - `POST /legacy/caisse/fiches/{sale_id}/void` now requires reason payload;
  - records audit on successful void;
  - preserves closed-day guard;
  - adds `GET /legacy/caisse/fiches/{sale_id}/audit`.
- `studio_suite/backend/tests/test_legacy_caisse_correction_audit.py`
  - new T-006 behavior tests.
- `studio_suite/backend/tests/test_legacy_caisse_fiche_correction.py`
  - updated T-005 regression tests for reason payload and audit table.

Frontend:

- `studio_suite/frontend/src/pages/LegacyCaissePage.tsx`
  - reason prompt before void;
  - audit history state/read path;
  - audit display in fiche list modal.

Control artifacts:

- `studio_suite/docs/tickets/006-correction-reason-audit-trail.md`
- `studio_suite/docs/flags/2026-07-05-t006-correction-reason-audit-trail.json`
- this handoff
- T-006 postmortem

## Validation performed

RED signal:

```bash
cd studio_suite/backend && .venv/bin/python -m pytest tests/test_legacy_caisse_correction_audit.py -q
```

Expected failure observed before implementation:

```text
ImportError: cannot import name 'get_fiche_audit'
```

Final checks:

```bash
cd studio_suite/backend && .venv/bin/python -m pytest tests/test_legacy_caisse_minimal_flow.py tests/test_legacy_caisse_cash_session.py tests/test_legacy_caisse_fiche_correction.py tests/test_legacy_caisse_correction_audit.py -q
```

Result:

```text
11 passed, 7 warnings
```

```bash
cd studio_suite/backend && .venv/bin/python -m compileall app
```

Result: PASS.

```bash
cd studio_suite/frontend && npm run build -- --outDir /tmp/studio-suite-vite-build --emptyOutDir
```

Result:

```text
✓ built in 25.45s
```

Runtime health:

```text
http://192.168.50.20:8003/health -> 200
http://192.168.50.20:8004/health -> 200
https://dev2.witold.ovh/health -> 200
```

## Scope guard

Not done:

- no production deployment;
- no merge to `master`;
- no branch-policy decision;
- no Deployment Authority assignment;
- no public booking changes;
- no fiscal/invoice correction semantics;
- no full accounting correction journal;
- no receipt/fiscal printing;
- no exploitation report suite;
- no WinDev/Bureau runtime reconstruction.

## PM review note

T-006 satisfies the approved bounded Objective and is ready for review/acceptance under the current PM operational authority boundary.
