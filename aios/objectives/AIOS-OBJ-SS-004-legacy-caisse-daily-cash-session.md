# AIOS-OBJ-SS-004 — Legacy CAISSE Daily Cash Session

Date: 2026-07-05
Status: APPROVED
Project: Studio Suite
Authority: Sponsor
Objective class: bounded feature / delivery slice

## Sponsor Decision

Sponsor approves the PM recommendation to continue Legacy CAISSE development with a bounded daily cash-session slice.

Approved direction:

```text
AIOS-OBJ-SS-004 — Legacy CAISSE Daily Cash Session
T-004 — Cash Session Lifecycle and Daily Summary
```

This approval authorizes preparation of the implementation package. Implementation starts only after explicit Sponsor execution instruction for T-004.

## Goal

Deliver a minimal operational day-cycle for Legacy CAISSE:

```text
open cash session → create fiches/payments → record expenses/presence → close cash session → see daily summary
```

The Objective should make the accepted T-003 cashier fiche flow usable inside a salon day of work, without expanding into full WinDev/Bureau reconstruction.

## Context

Accepted baseline:

- AIOS-OBJ-SS-003 / T-003 accepted by Sponsor;
- accepted implementation commit: `d715404 impl(t003): harden legacy caisse minimal flow`;
- operational branch: `feature/legacy-caisse-flow`;
- Deployment Authority unresolved;
- production deployment and merge to `master` remain separate authority decisions.

Legacy CAISSE current documented core scope includes:

- cashier fiche entry with legacy staff and service codes;
- bundles/forfaits, discounts, and payment capture;
- current-month fiche list;
- salon expenses, cash session, and staff presence;
- tenant module license `LEGACY_CAISSE` and salon access checks.

T-003 covered the minimal fiche create/list and core guards. T-004 extends that into the smallest useful cash-day lifecycle.

## Scope

In scope:

1. Cash session lifecycle:
   - open a cash session for tenant/salon/business date;
   - store opening cash;
   - close the session with closing cash;
   - record open/close user and timestamp where the model supports it.

2. Lifecycle rules:
   - one cash session per tenant/salon/business date;
   - cannot close a missing session;
   - cannot normally edit a closed session without an explicit correction path;
   - clear 4xx responses for invalid lifecycle transitions.

3. Daily summary:
   - service gross;
   - retail/product gross;
   - discount total;
   - payments by method;
   - cash payments;
   - expenses total, with cash expenses where supported;
   - expected cash = opening cash + cash payments - cash expenses;
   - closing cash;
   - cash difference.

4. UI integration:
   - use the existing `LegacyCaissePage` surface;
   - keep the UI minimal;
   - expose open/close day and daily summary enough for operator review;
   - no redesign.

5. Tests and evidence:
   - backend tests for lifecycle and summary calculations;
   - frontend build;
   - backend compileall;
   - runtime health checks when environment is available;
   - handoff/postmortem if implementation is delegated.

## Explicit Exclusions

This Objective does not include:

- full WinDev/Bureau reconstruction;
- WDD/FIC/NDX runtime checks;
- CAISSE-to-Bureau transfer;
- exploitation reports;
- fiscal printer / fiskalizacja;
- printing receipts;
- file database synchronization;
- broad report redesign;
- production deployment;
- merge/promote to `master`;
- assigning Deployment Authority;
- public booking changes;
- AIOS governance changes.

## Acceptance Criteria

### AC-1 — Cash session can be opened

A valid operational user can open a cash session for a tenant-scoped salon and business date with an opening cash amount.

### AC-2 — Duplicate session is blocked

A second open/create operation for the same tenant/salon/business date does not create a duplicate session and returns predictable behavior.

### AC-3 — Cash session can be closed

A valid operational user can close an existing open cash session with a closing cash amount. Close metadata is recorded where model fields exist.

### AC-4 — Closed session is protected

A normally closed session cannot be silently overwritten or reopened by the ordinary open/update path. Any correction path must be explicit and documented.

### AC-5 — Daily summary is available

The API and UI expose a minimal daily summary for the salon/business date including sales, payments, expenses, expected cash, closing cash, and difference.

### AC-6 — Tenant/salon/module boundaries are preserved

All new or changed paths preserve:

- tenant isolation;
- salon access validation;
- `LEGACY_CAISSE` module/license guard;
- no public booking exposure.

### AC-7 — Verification passes

Required checks:

```text
git status --short
backend targeted tests for T-004 lifecycle/summary
backend compileall for studio_suite/backend/app
frontend build
runtime health checks for backend/backend_public/public health when environment is available
```

### AC-8 — Authority boundary preserved

This Objective does not authorize deployment, merge to `master`, branch-policy decision, or broad Legacy/Bureau reconstruction.

## Authority Boundary

Project Authority: Sponsor
Acceptance Authority: Sponsor
Deployment Authority: unresolved
Operational branch for this Objective: `feature/legacy-caisse-flow`

PM may prepare implementation package, verify evidence, and issue recommendation.
Implementation/delegation starts only after explicit execution instruction from Sponsor.
Final acceptance remains with Sponsor.
