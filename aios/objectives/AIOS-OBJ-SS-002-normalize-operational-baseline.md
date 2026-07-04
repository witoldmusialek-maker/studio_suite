# AIOS-OBJ-SS-002 — Normalize Studio Suite Operational Baseline

Date: 2026-07-04
Status: APPROVED
Project: Studio Suite
Authority: Sponsor
Objective class: operational cleanup / pre-delivery

## Sponsor Decision

Sponsor approves AIOS-OBJ-SS-002 as the next bounded operational cleanup Objective after acceptance of AIOS-OBJ-SS-001.

## Goal

Normalize Studio Suite's operational baseline so the project can become predictable enough for a future first feature/delivery Objective.

This Objective cleans up known operational blockers found during AIOS-OBJ-SS-001. It does not authorize feature delivery.

## Context

AIOS-OBJ-SS-001 established the current operational baseline and was accepted by Sponsor.

Accepted PM verdict from AIOS-OBJ-SS-001:

```text
Not ready — further operational cleanup required
```

Accepted blockers:

- backend syntax check fails because of BOM in two legacy CAISSE Python files;
- smoke/auth gate is stale relative to current auth/TOTP reality;
- deployment docs/scripts contain stale references and assumptions;
- operational branch remains `feature/legacy-caisse-flow`;
- live target is `192.168.50.20`;
- merge/promotion to `master` is not yet authorized.

## Scope

In scope:

1. Remove BOM from:
   - `studio_suite/backend/app/api/v1/legacy_caisse.py`;
   - `studio_suite/backend/app/schemas/legacy_caisse.py`.

2. Normalize smoke/auth procedure:
   - make the smoke gate reflect current auth/TOTP reality;
   - avoid embedding secrets;
   - preserve a usable non-secret health/smoke baseline.

3. Normalize operational deployment references:
   - align relevant deployment docs/scripts with current target `192.168.50.20` where evidence supports it;
   - identify stale `192.168.200.116`, `dev1`, and `master` assumptions;
   - keep cleanup minimal and operational.

4. Preserve branch policy during cleanup:
   - continue on `feature/legacy-caisse-flow`;
   - do not merge/promote to `master` inside this Objective.

5. Rerun baseline verification:
   - backend syntax check;
   - frontend build to temporary output;
   - runtime health checks;
   - smoke/auth procedure as updated.

6. Issue PM closeout:
   - readiness verdict;
   - branch policy recommendation;
   - deployment target recommendation;
   - whether Studio Suite is ready for first feature/delivery Objective.

## Explicit Exclusions

This Objective does not include:

- feature delivery;
- domain refactoring;
- new legacy CAISSE functionality;
- WinDev migration;
- production deployment;
- merge to `master`;
- assigning Deployment Authority;
- AIOS governance changes;
- broad documentation rewrite;
- broad test strategy redesign;
- delegation unless Sponsor separately authorizes it.

## Acceptance Criteria

### AC-1 — Backend syntax blocker removed

Backend AST syntax check passes for `studio_suite/backend/app` without writing `.pyc` files.

### AC-2 — Smoke/auth baseline normalized

Smoke/auth procedure is updated so future PM review can distinguish:

- public health/runtime readiness;
- authenticated operational smoke requiring credentials/TOTP;
- missing credentials vs application failure.

No secrets are committed.

### AC-3 — Deployment references normalized or classified

Known stale operational references are either:

- updated to current evidence-backed target `192.168.50.20`, or
- explicitly marked as historical/stale/deferred.

### AC-4 — Dirty deployment-script changes resolved within Objective scope

Existing dirty changes in:

- `deploy.ps1`;
- `studio_suite/scripts/deploy-dev2.ps1`;

are either committed as part of an accepted cleanup package or consciously superseded/reverted with evidence.

### AC-5 — Baseline verification rerun

PM reruns and records:

- git status;
- backend syntax check;
- frontend build to temporary output;
- docker compose/runtime health;
- updated smoke/auth check.

### AC-6 — Operational readiness verdict issued

PM issues one verdict:

```text
Ready for first feature/delivery Objective
Ready after Sponsor authority decision
Not ready — further cleanup required
```

### AC-7 — Authority boundary preserved

The Objective preserves:

- Project Authority: Sponsor;
- Acceptance Authority: Sponsor;
- Deployment Authority: unresolved;
- no feature delivery;
- no merge to `master` without Sponsor decision;
- no production deployment.

## Authority Boundary

PM may modify files only within this approved operational cleanup scope.

PM may not independently:

- start feature delivery;
- deploy to production;
- merge/promote to `master`;
- assign Deployment Authority;
- expand scope into domain implementation;
- change AIOS governance.
