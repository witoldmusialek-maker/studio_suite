# AIOS-OBJ-SS-001 — Establish Studio Suite Operational Baseline

Date: 2026-07-04
Status: APPROVED
Project: Studio Suite
Authority: Sponsor
Objective class: operational readiness / pre-delivery

## Sponsor Decision

Sponsor approved AIOS-OBJ-SS-001 as the first operational Objective for Studio Suite.

Sponsor refinement recorded:

> Frame the Objective as establishing the project's operational baseline rather than restoring a previous state, since current operational truth has already evolved beyond historical assumptions.

This refinement does not block approval.

## Goal

Establish a predictable operational baseline for Studio Suite so PM, Sponsor, and any future implementer can safely prepare the first delivery Objective without guessing branch state, deployment target, script status, or runtime health.

This is a pre-delivery Objective. It does not authorize feature delivery.

## Context

Studio Suite is onboarded into AIOS and has reached Minimum Viable Understanding.

Current known state:

- operational runtime aligns with `feature/legacy-caisse-flow`;
- `master` remains remote default but is stale relative to the current runtime shape;
- live runtime target is `192.168.50.20`;
- historical `192.168.200.116` references remain in docs/scripts/configs;
- dirty deployment script changes point from `192.168.200.116` to `192.168.50.20`;
- Project Authority and Acceptance Authority remain with Sponsor;
- Deployment Authority remains unresolved.

## Scope

In scope:

1. Confirm the current operational baseline:
   - active branch/runtime relationship;
   - active deployment target;
   - docker compose state;
   - health endpoints;
   - public health endpoint.

2. Assess deployment scripts and docs:
   - identify current vs stale scripts/docs;
   - assess existing dirty deployment-script changes;
   - recommend minimal cleanup needed for predictable operations.

3. Prepare branch policy recommendation:
   - continue on `feature/legacy-caisse-flow`;
   - promote/merge to `master`;
   - or another minimal branch policy.

4. Define minimum verification path for future delivery:
   - backend compile;
   - frontend build;
   - docker compose health;
   - smoke direct/public;
   - manual checklist when needed.

5. Issue operational readiness verdict:
   - `Ready for first delivery Objective`;
   - `Ready after authority decision`;
   - `Not ready — further operational cleanup required`.

## Explicit Exclusions

This Objective does not include:

- feature delivery;
- domain refactoring;
- legacy CAISSE implementation;
- WinDev migration;
- AIOS governance changes;
- delegation;
- production deployment;
- merge to `master` without Sponsor decision;
- accepting dirty deployment-script changes without Sponsor decision;
- assigning Deployment Authority without Sponsor decision.

## Acceptance Criteria

### AC-1 — Current runtime baseline confirmed

PM provides evidence for:

- active branch/runtime relationship;
- active deployment target;
- docker compose status;
- backend/backend_public health;
- public health endpoint.

### AC-2 — Deployment scripts assessed

PM identifies:

- which deployment scripts/docs are current;
- which are stale;
- which require correction;
- whether current dirty deployment-script changes should be accepted.

### AC-3 — Branch policy recommendation prepared

PM recommends one branch policy option for Sponsor decision.

### AC-4 — Verification path defined

PM defines the minimal verification path required before future delivery Objectives.

### AC-5 — Operational readiness verdict issued

PM issues one verdict:

```text
Ready for first delivery Objective
Ready after authority decision
Not ready — further operational cleanup required
```

### AC-6 — Authority boundary preserved

The Objective preserves:

- Project Authority: Sponsor;
- Acceptance Authority: Sponsor;
- Deployment Authority: unresolved;
- no delivery without explicit approval.

## Authority Boundary

PM may analyze, verify, document, and recommend.

PM may not independently:

- accept branch policy;
- accept dirty deployment-script changes;
- deploy;
- start feature delivery;
- delegate implementation;
- assign Deployment Authority.
