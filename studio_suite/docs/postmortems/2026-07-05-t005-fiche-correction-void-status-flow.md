# Postmortem — T-005 Fiche Correction / Void / Status Flow

Date: 2026-07-05
Status: ready-for-review
Objective: AIOS-OBJ-SS-005 — Legacy CAISSE Fiche Correction / Void / Status Flow

## What happened

T-005 hardened the existing `void_fiche` behavior after T-004 introduced cash-session closing. The existing endpoint already marked sale/payment as void, and daily summary already ignored non-completed payments. The missing behavior was closed-day protection and explicit regression coverage.

## TDD notes

RED evidence:

```text
cd studio_suite/backend && .venv/bin/python -m pytest tests/test_legacy_caisse_fiche_correction.py -q
```

Initial result:

```text
2 passed, 1 failed
Failed: DID NOT RAISE HTTPException
```

The failing test proved that voiding after cash-session close was still allowed.

GREEN evidence:

```text
8 passed, 7 warnings
```

## Issues found

1. `void_fiche` did not protect closed cash days.
2. Duplicate void behavior was not documented/tested.
3. The UI showed a fiche list but had no operator action to void a mistaken fiche.

## Fix applied

- Added closed-day guard in `void_fiche` using the sale date and `CashierCashSession` status.
- Made duplicate void idempotent: if sale is already `VOID`, return `VOID` without further mutation.
- Kept payment consistency by setting associated `Payment.status` to `void`.
- Added regression tests for:
  - void status/payment update;
  - daily summary exclusion;
  - duplicate void idempotency;
  - blocked void after cash-session close.
- Added minimal UI action from fiche list.

## Important implementation choice

The conservative rule is:

```text
ordinary void is allowed only before the cash day is closed
```

After close, correction should be a separate explicit correction path with audit semantics. T-005 intentionally does not invent a full correction journal.

## What stayed out of scope

- full audit/accounting correction journal;
- correction reason persistence;
- fiscal printing;
- receipt printing;
- exploitation reporting;
- CAISSE-to-Bureau transfer;
- WDD/FIC/NDX runtime checks;
- public booking changes;
- production deployment;
- merge to `master`.

## Follow-up recommendations

1. Next product slice can be `T-006 — Correction reason / audit trail` if auditability is needed before deployment.
2. If Sponsor wants user-facing readiness first, consider a small UI hardening slice for explicit buttons and error display instead of click-to-void.
3. Keep branch/deployment policy separate from product delivery acceptance.
