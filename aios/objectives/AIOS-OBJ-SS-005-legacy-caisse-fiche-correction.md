# AIOS-OBJ-SS-005 — Legacy CAISSE Fiche Correction / Void / Status Flow

Date: 2026-07-05
Status: APPROVED
Project: Studio Suite
Authority: Sponsor
Objective class: bounded feature / delivery slice

## Sponsor Decision

Sponsor approves the PM recommendation to continue Legacy CAISSE development with a bounded correction/status slice.

Approved direction:

```text
AIOS-OBJ-SS-005 — Legacy CAISSE Fiche Correction / Void / Status Flow
T-005 — Fiche Correction / Void / Status Flow
```

This approval authorizes preparation of the implementation package. Implementation starts only after explicit Sponsor execution instruction for T-005.

## Goal

Make Legacy CAISSE corrections safe and auditable after T-003/T-004 established creation, day session, close, and summary behavior.

The core operational question:

```text
If a cashier made a mistake, can the salon correct/void it safely without silently corrupting a closed cash day?
```

## Context

Accepted baseline:

- AIOS-OBJ-SS-003 / T-003 accepted: minimal fiche create/list flow;
- AIOS-OBJ-SS-004 / T-004 accepted: cash-session lifecycle and daily summary;
- accepted implementation commits:
  - `d715404 impl(t003): harden legacy caisse minimal flow`;
  - `fdf9172 impl(t004): add legacy caisse cash day summary`;
- operational branch: `feature/legacy-caisse-flow`;
- Deployment Authority unresolved;
- production deployment and merge to `master` remain separate authority decisions.

Current risk after T-004:

- day close now exists, therefore fiche corrections must be explicit;
- silent sale/payment mutation after close would undermine the daily summary;
- the existing `void_fiche` endpoint marks sale/payment void but needs stronger lifecycle semantics and test coverage.

## Scope

In scope:

1. Fiche status lifecycle:
   - preserve `COMPLETED`, `PENDING`, and `VOID` semantics;
   - define allowed status transitions for Legacy CAISSE;
   - block invalid or silent transitions with predictable 4xx responses.

2. Safe void flow:
   - void an existing fiche/sale within tenant/salon boundary;
   - void associated payment rows consistently;
   - ensure voided payments/sales are excluded from daily summary where appropriate;
   - require/record a correction reason where model or minimal extension supports it.

3. Closed cash-session guard:
   - ordinary void/correction must not silently alter a closed cash day;
   - either block corrections after cash-session close, or require an explicit correction mode documented in the handoff;
   - keep initial implementation conservative if model lacks audit fields.

4. UI integration:
   - expose minimal void/correction action from the existing fiche list;
   - no redesign;
   - show failure messages for closed-day or invalid transition cases.

5. Tests and evidence:
   - backend tests for valid void, duplicate void/idempotency or conflict, closed-day protection, and summary exclusion;
   - regression tests for T-003/T-004 behavior;
   - frontend build;
   - backend compileall;
   - runtime health checks when environment is available.

## Explicit Exclusions

This Objective does not include:

- full WinDev/Bureau reconstruction;
- WDD/FIC/NDX runtime checks;
- CAISSE-to-Bureau transfer;
- fiscal printing;
- receipt printing;
- full correction journal/accounting subsystem;
- exploitation reports;
- production deployment;
- merge/promote to `master`;
- assigning Deployment Authority;
- public booking changes;
- AIOS governance changes.

## Acceptance Criteria

### AC-1 — Existing fiche can be voided safely

A valid operational user can void an existing tenant/salon-scoped Legacy CAISSE fiche. Associated payment records are made non-active/non-counting according to the chosen model semantics.

### AC-2 — Voided fiche is not counted in cash summary

A voided completed sale/payment no longer contributes to the daily cash-session summary totals.

### AC-3 — Duplicate void is predictable

A second void operation on an already voided fiche is either idempotent or returns a predictable conflict. The chosen behavior must be tested and documented.

### AC-4 — Closed cash day is protected

Ordinary correction/void action does not silently mutate a closed cash day. It is blocked or routed through an explicit correction path, with test coverage.

### AC-5 — Invalid transitions are blocked

Unsupported status transitions are rejected with clear 4xx behavior and without partial persistence.

### AC-6 — Minimal UI action exists

The existing Legacy CAISSE fiche list exposes a minimal void/correction action without redesign, and refreshes list/summary state afterward.

### AC-7 — Tenant/salon/module boundaries are preserved

All new or changed paths preserve:

- tenant isolation;
- salon access validation;
- `LEGACY_CAISSE` module/license guard;
- no public booking exposure.

### AC-8 — Verification passes

Required checks:

```text
git status --short
backend targeted tests for T-003/T-004/T-005
backend compileall for studio_suite/backend/app
frontend build
runtime health checks for backend/backend_public/public health when environment is available
```

### AC-9 — Authority boundary preserved

This Objective does not authorize deployment, merge to `master`, branch-policy decision, or broad Legacy/Bureau reconstruction.

## Authority Boundary

Project Authority: Sponsor
Acceptance Authority: Sponsor
Deployment Authority: unresolved
Operational branch for this Objective: `feature/legacy-caisse-flow`

PM may prepare implementation package, verify evidence, and issue recommendation.
Implementation/delegation starts only after explicit execution instruction from Sponsor.
Final acceptance remains with Sponsor.
