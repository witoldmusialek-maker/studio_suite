# Postmortem — T-006 Correction Reason / Audit Trail

Date: 2026-07-05
Status: ready-for-review
Objective: AIOS-OBJ-SS-006 — Legacy CAISSE Correction Reason / Audit Trail

## Summary

T-006 was implemented as a bounded pilot-safety hardening slice after T-005 acceptance and PM operational authority clarification.

The implementation adds an explicit audit table and a minimal read path rather than overloading `Sale` or `Payment` fields.

## What went well

- TDD RED was observed before implementation: the new correction-audit test failed because `get_fiche_audit` did not exist.
- The existing T-005 void lifecycle provided a clean insertion point for reason capture and audit persistence.
- Daily summary behavior remained stable because T-005 already excluded non-completed payments.
- Frontend impact stayed minimal: prompt reason, call existing void path with payload, display history in existing fiche modal.

## Issues encountered

### Existing T-005 tests lacked the new audit table in SQLite setup

After adding audit persistence, older T-005 regression tests failed with:

```text
sqlite3.OperationalError: no such table: cashier_correction_audits
```

Cause:

- slice tests use explicit table lists for SQLite in-memory setup;
- the new table was correctly added to the new T-006 test fixture but not initially added to the T-005 fixture.

Resolution:

- imported `CashierCorrectionAudit` in `test_legacy_caisse_fiche_correction.py`;
- added `CashierCorrectionAudit.__table__` to the explicit table setup.

## Design choices

### Explicit audit model

A new `CashierCorrectionAudit` model was chosen because the ticket required durable actor/reason/status history.

Fields:

- tenant_id;
- salon_id;
- sale_id;
- actor_user_id;
- action_type;
- reason;
- previous_status;
- new_status;
- created_at.

### Reason required before mutation

The void path validates a non-empty reason before checking duplicate/closed-day flow. This keeps the operator flow explicit and prevents unaudited correction intent.

### Closed-day failure does not audit success

Closed-day void still returns 409 and does not write a success audit record. This preserves T-005 semantics.

### Duplicate void remains idempotent

Duplicate void returns VOID response without applying another mutation. It does not create an additional success audit record.

## Verification

Final checks passed:

```text
11 passed, 7 warnings
backend compileall PASS
frontend build PASS
health endpoints 200/200/200
```

## Out of scope retained

- no accounting journal;
- no fiscal correction semantics;
- no receipt/fiscal printing;
- no production deploy;
- no merge to `master`;
- no public booking changes.

## Follow-up candidates

- T-007 Operator UX hardening: replace `window.prompt` with a controlled modal and safer action layout.
- T-008 Daily close report export/print-lite.
- T-009 Pilot readiness review.
