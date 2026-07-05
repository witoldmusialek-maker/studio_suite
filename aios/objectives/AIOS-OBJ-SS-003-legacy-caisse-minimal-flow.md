# AIOS-OBJ-SS-003 — Legacy CAISSE Minimal Flow

Date: 2026-07-05
Status: APPROVED
Project: Studio Suite
Authority: Sponsor
Objective class: first feature / delivery slice

## Sponsor Decision

Sponsor approves Legacy CAISSE minimal flow as the first Studio Suite delivery Objective after acceptance of AIOS-OBJ-SS-002.

Approved PM recommendation:

```text
Use feature/legacy-caisse-flow as the operational branch for this first delivery.
Do not merge/promote to master inside this Objective.
Deliver one minimal end-to-end legacy cashier flow, preserving tenant isolation, module licensing, and public/private separation.
```

## Goal

Deliver and verify a minimal end-to-end Legacy CAISSE cashier workflow for salon operations.

The Objective should prove that the modern Studio Suite stack can support the first usable legacy cashier slice using the existing tenant, salon, staff, service, bundle/product, sale, and payment model.

## Context

Accepted current baseline:

- AIOS-OBJ-SS-002 accepted by Sponsor;
- operational branch: `feature/legacy-caisse-flow`;
- live target: `192.168.50.20`;
- runtime health and public health pass;
- deployment target and operational references normalized;
- feature delivery was not previously authorized and is now authorized only for this bounded Objective.

Legacy CAISSE transition scope from `studio_suite/docs/legacy-caisse-transition-plan.md`:

- cashier fiche entry with legacy staff and service codes;
- bundles/forfaits, discounts, and payment capture;
- current-month fiche list;
- salon expenses, cash session, and staff presence;
- tenant module license `LEGACY_CAISSE` and salon access checks.

This Objective takes the smallest useful subset of that scope.

## Minimal Delivery Slice

In scope:

1. Verify or implement a minimal operational UI/API path for:
   - selecting tenant-scoped salon context;
   - entering a cashier fiche using legacy staff/service code semantics where already modeled;
   - adding at least one service or product/bundle line;
   - applying a discount if the existing domain supports it;
   - capturing payment method/amount;
   - persisting the sale/payment data tenant-safely;
   - listing current-month fiches for that salon.

2. Preserve required guards:
   - tenant isolation;
   - salon access validation;
   - `LEGACY_CAISSE` module/license enforcement where the project model supports it;
   - no public booking coupling;
   - no committed secrets or real personal data.

3. Add or update tests for the delivered path:
   - backend test(s) for tenant/salon/license guard where feasible;
   - backend test(s) for creating/listing the minimal cashier fiche;
   - frontend build verification;
   - runtime health verification.

4. Produce implementation evidence:
   - changed files summary;
   - validation commands and results;
   - limitations / deferred scope;
   - review handoff.

## Explicit Exclusions

This Objective does not include:

- full WinDev/Bureau reconstruction;
- WDD/FIC/NDX runtime checks;
- CAISSE-to-Bureau transfer;
- exploitation reports;
- file database synchronization;
- broad legacy migration/import rewrite;
- production deployment;
- merge/promote to `master`;
- assigning Deployment Authority;
- changing AIOS governance;
- weakening public/private separation;
- generalized rewrite of payments, inventory, reporting, or auth.

## Acceptance Criteria

### AC-1 — Minimal cashier flow works end-to-end

A user with valid operational access can complete the minimal Legacy CAISSE cashier path in the operational surface, and the resulting data is persisted and visible in the current-month fiche list.

### AC-2 — Tenant/salon boundaries preserved

The delivered API/UI path remains tenant-aware and validates salon access. Cross-tenant or unauthorized salon access is blocked or covered by existing access controls.

### AC-3 — Module/license boundary preserved

The `LEGACY_CAISSE` module/license guard is preserved or explicitly verified against the current licensing model. If the existing implementation lacks a usable guard, the gap is documented and the Objective may only pass with Sponsor-visible limitation.

### AC-4 — Public/private separation preserved

No Legacy CAISSE operational endpoint or UI is exposed through the public booking surface.

### AC-5 — Verification passes

Required checks:

```text
git status --short
backend targeted tests for legacy CAISSE path / affected APIs
backend syntax check for studio_suite/backend/app
frontend build
runtime health checks for backend/backend_public
public health check
```

If authenticated manual smoke requires credentials/TOTP, report it as a controlled environment requirement and do not commit secrets.

### AC-6 — Review evidence prepared

Implementation must produce a review handoff documenting:

- scope delivered;
- files changed;
- tests/checks run;
- known limitations;
- out-of-scope items not touched.

### AC-7 — Authority boundary preserved

This Objective approves the bounded delivery scope and implementation handoff package.

It does not authorize:

- production deployment;
- merge/promote to `master`;
- assigning Deployment Authority;
- unbounded domain refactor;
- AIOS governance changes.

## Authority Boundary

Project Authority: Sponsor
Acceptance Authority: Sponsor
Deployment Authority: unresolved
Operational branch for this Objective: `feature/legacy-caisse-flow`

PM may prepare the implementation package, verify evidence, and issue a recommendation.
Implementation/delegation starts only after an explicit execution instruction from Sponsor.
Final acceptance remains with Sponsor.
