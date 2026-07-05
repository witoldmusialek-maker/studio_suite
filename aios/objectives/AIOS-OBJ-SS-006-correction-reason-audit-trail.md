# AIOS-OBJ-SS-006 — Legacy CAISSE Correction Reason / Audit Trail

Date: 2026-07-05
Status: APPROVED
Project: Studio Suite
Authority: Sponsor
Objective class: bounded feature / pilot-safety hardening slice

## Sponsor Decision

Sponsor accepted the Controlled Pilot Track and authorized PM to prepare T-006 after T-005 acceptance.

T-005 acceptance is recorded in:

```text
aios/objectives/AIOS-OBJ-SS-005-acceptance.md
```

Therefore PM is authorized to prepare:

```text
AIOS-OBJ-SS-006 — Legacy CAISSE Correction Reason / Audit Trail
T-006 — Correction Reason / Audit Trail
```

This approval authorizes preparation of the implementation package. Implementation starts only after explicit Sponsor execution instruction for T-006.

## Goal

Make Legacy CAISSE correction/void actions auditable enough for controlled pilot use.

The core operational question:

```text
When a fiche is voided or corrected, can the manager see who did it, when, and why, without needing database inspection?
```

## Context

Accepted baseline:

- T-003 accepted: minimal fiche create/list flow;
- T-004 accepted: cash-session lifecycle and daily summary;
- T-005 accepted: safe correction/void guard, duplicate void idempotency, closed-day protection;
- strategic direction accepted: Controlled Pilot Track;
- operational branch: `feature/legacy-caisse-flow`;
- production deployment and merge to `master` remain separate decisions;
- Deployment Authority remains unresolved.

T-005 intentionally deferred a full correction journal. T-006 should add the smallest useful audit trail for pilot safety, not a complete accounting subsystem.

## Scope

In scope:

1. Correction/void reason capture:
   - require or accept a reason for void/correction action;
   - persist reason in a minimal auditable structure;
   - associate the reason with sale/fiche and acting user.

2. Audit metadata:
   - record action type, timestamp, actor/user id, tenant id, salon id, sale id;
   - record previous and resulting status where practical;
   - keep schema small and explicit.

3. Audit read surface:
   - expose minimal backend read path for a fiche correction/audit history;
   - allow manager/operator to inspect correction reason from Legacy CAISSE context.

4. UI integration:
   - replace bare click-to-void with explicit action requiring reason;
   - show the reason/history minimally in the existing Legacy CAISSE UI;
   - no redesign.

5. Regression safety:
   - T-003 create/list remains compatible;
   - T-004 daily summary remains compatible;
   - T-005 void/closed-day guard remains compatible;
   - public booking remains untouched.

## Explicit Exclusions

This Objective does not include:

- full accounting/correction journal;
- invoice/fiscal correction semantics;
- fiscal printing;
- receipt printing;
- full exploitation reporting;
- CAISSE-to-Bureau transfer;
- WDD/FIC/NDX runtime checks;
- production deployment;
- merge/promote to `master`;
- assigning Deployment Authority;
- public booking changes;
- broad UI redesign.

## Acceptance Criteria

### AC-1 — Void requires or records a reason

A void/correction action records a human-readable reason linked to the fiche/sale.

### AC-2 — Audit metadata is persisted

Audit record includes at least:

- tenant id;
- salon id;
- sale id;
- actor/user id;
- action type;
- reason;
- timestamp;
- previous status;
- new status.

### AC-3 — Audit history can be read

Backend exposes a minimal read path for correction/audit history for a fiche/sale within tenant/salon boundary.

### AC-4 — UI uses explicit reason flow

Legacy CAISSE UI no longer relies only on click-to-void. It asks for a reason and refreshes list/summary/audit state after success.

### AC-5 — Closed-day protection remains intact

Ordinary void/correction after cash-session close is still blocked and does not create misleading audit success records.

### AC-6 — Daily summary remains correct

Voided payments remain excluded from daily summary exactly as in T-005.

### AC-7 — Boundaries preserved

Tenant isolation, salon access validation, `LEGACY_CAISSE` module/license guard, and public/private separation remain preserved.

### AC-8 — Verification passes

Required checks:

```text
git status --short
backend targeted tests for T-003/T-004/T-005/T-006
backend compileall for studio_suite/backend/app
frontend build
runtime health checks for backend/backend_public/public health when environment is available
```

## Authority Boundary

Project Authority: Sponsor
Acceptance Authority: Sponsor
Deployment Authority: unresolved
Operational branch for this Objective: `feature/legacy-caisse-flow`

PM may prepare implementation package, verify evidence, and issue recommendation.
Implementation/delegation starts only after explicit execution instruction from Sponsor.
Final acceptance remains with Sponsor.
