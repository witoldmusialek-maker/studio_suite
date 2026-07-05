# Studio Suite Strategic Recommendation — Further Application Development

Date: 2026-07-05
Status: accepted-by-sponsor
Project: Studio Suite
Authority: Sponsor
Prepared by: AIOS PM

## Sponsor mandate

Sponsor grants PM mandate to prepare strategic recommendations for further development of the application.

Authority boundary:

- This recommendation does not itself authorize production deployment.
- This recommendation does not itself authorize merge/promote to `master`.
- This recommendation does not assign Deployment Authority.
- Individual implementation Objectives still require explicit Sponsor approval.
- Final acceptance remains with Sponsor unless explicitly delegated.

Engine policy note:

```text
sponsor_engine_required: true
sponsor_engine_specified: not specified in this request
requirement_satisfied: not applicable — no model-specific execution was requested; PM prepared recommendation in active session
```

## Current evidence baseline

Accepted / completed evidence:

```text
T-003 — Legacy CAISSE Minimal Flow — accepted
T-004 — Cash Session Lifecycle and Daily Summary — accepted
T-005 — Fiche Correction / Void / Status Flow — implemented, ready-for-review
```

Current branch/runtime evidence:

```text
Operational branch: feature/legacy-caisse-flow
Remote default branch: origin/master
Runtime health evidence remains positive for backend/backend_public/public health
Deployment Authority: unresolved
Production deployment: not authorized
Merge to master: not authorized
```

## Strategic diagnosis

Studio Suite has moved from onboarding/evidence collection into a real product-development path. The application is no longer only a modernization shell: Legacy CAISSE now has the core operational spine of a salon cash day:

```text
create fiche/sale
→ open cash session
→ sales/expenses
→ close cash session
→ daily summary
→ safe void/correction guard
```

The strategic risk is no longer “can we build this at all?” but:

```text
Can we evolve this into a pilot-ready salon operations module without collapsing into full WinDev/Bureau reconstruction, uncontrolled scope, or unsafe deployment?
```

## Recommended strategic direction

PM recommendation:

```text
Adopt a Controlled Pilot Track for Studio Suite, centered on the modern Salon Module / Legacy CAISSE transition, with explicit release gates before branch promotion or deployment.
```

This means:

1. Continue product development through bounded vertical slices.
2. Treat Legacy CAISSE as the transition surface toward a modern Salon Module, not as a goal to preserve WinDev architecture.
3. Separate product acceptance from deployment/branch policy.
4. Build enough audit, reporting, and UI stability to support an internal pilot before production decisions.
5. Avoid broad rewrites, full Bureau reconstruction, and premature merge-to-master.

## Strategic decisions requested

### Decision 1 — Product track

Recommendation: accept **Controlled Pilot Track** as the development mode for the next phase.

| Option | PM assessment |
|---|---|
| Continue ad hoc tickets | Too reactive; risks losing product coherence. |
| Full rewrite / full WinDev reconstruction | Too large, high-risk, and contrary to current evidence. |
| Controlled Pilot Track | Recommended: bounded slices, measurable readiness, avoids premature deployment. |

Requested Sponsor decision:

```text
Approve Controlled Pilot Track as the strategic development direction.
```

### Decision 2 — Branch policy

Recommendation: keep `feature/legacy-caisse-flow` as the active operational integration branch for now.

Do not merge/promote to `master` yet.

Rationale:

- accepted work is accumulating coherently on this branch;
- `master` is stale relative to current runtime shape;
- branch promotion should follow a release-readiness gate, not happen incidentally;
- keeping the branch avoids mixing product delivery with deployment policy.

Requested Sponsor decision:

```text
Keep feature/legacy-caisse-flow as the active integration branch until pilot-readiness review.
```

### Decision 3 — Deployment authority

Recommendation: designate Deployment Authority before any production/staging deployment decision.

Until then:

```text
No production deploy.
No implicit deployment from accepted implementation.
Runtime health is evidence, not authority.
```

Requested Sponsor decision:

```text
Defer deployment until Deployment Authority is named and release gate is passed.
```

### Decision 4 — Next delivery sequence

Recommendation: complete T-005 acceptance first, then move into a short pilot-readiness hardening sequence.

Proposed sequence:

| Step | Objective / ticket | Purpose |
|---:|---|---|
| 0 | Accept or reject T-005 | Close current correction/void slice. |
| 1 | T-006 — Correction reason / audit trail | Make void/correction auditable enough for pilot use. |
| 2 | T-007 — Operator UX hardening | Replace click-to-void/minimal controls with explicit, safer operator actions. |
| 3 | T-008 — Daily close report export/print-lite | Produce reviewable end-of-day evidence for manager. |
| 4 | T-009 — Pilot readiness review | Decide whether branch is ready for staging/pilot/deployment policy. |

Requested Sponsor decision:

```text
Authorize PM to prepare T-006 after T-005 acceptance, unless Sponsor chooses branch/deployment policy first.
```

## Recommended roadmap

### Phase A — Operational core, nearly complete

Status: mostly delivered.

Includes:

- T-003 fiche create/list;
- T-004 cash day lifecycle and daily summary;
- T-005 correction/void protection, pending acceptance.

Exit criterion:

```text
T-005 accepted by Sponsor.
```

### Phase B — Pilot safety hardening

Goal: make the module safe enough for controlled internal/pilot use.

Recommended tickets:

1. `T-006 — Correction reason / audit trail`
   - record who/when/why for void/correction;
   - do not build full accounting journal yet.
2. `T-007 — Operator UX hardening`
   - explicit buttons/actions;
   - better closed-day and void error display;
   - safer confirmation flows.
3. `T-008 — Daily close report export/print-lite`
   - manager-facing daily close evidence;
   - no full exploitation reports.

Exit criterion:

```text
A manager can review a day close and corrections without inspecting the database.
```

### Phase C — Pilot readiness gate

Goal: decide whether the module is ready for controlled staging/pilot deployment.

Recommended Objective:

```text
AIOS-OBJ-SS-009 — Studio Suite Pilot Readiness Review
```

Review gates:

- backend tests for Legacy CAISSE core pass;
- frontend build passes;
- runtime health passes;
- public/private boundary verified;
- smoke path documented;
- Deployment Authority named;
- rollback/non-deploy policy explicit;
- branch promotion recommendation prepared.

Exit criterion:

```text
Sponsor receives one recommendation: pilot-ready / not pilot-ready / pilot-ready after named blockers.
```

### Phase D — Broader Salon Module expansion

Only after pilot readiness:

- richer reports;
- product/catalog refinements;
- staff/presence integration;
- stock/inventory coupling;
- SMS/client communication integration;
- eventual branch/deployment policy stabilization.

## What not to do now

Do not start these yet:

- full WinDev/Bureau reconstruction;
- WDD/FIC/NDX runtime dependency;
- exploitation report suite;
- fiscal printer integration;
- production deployment;
- merge to `master`;
- broad UI redesign;
- rewriting unrelated modules.

These may become valid later, but they are not the next strategic move.

## PM recommendation in one sentence

```text
Accept the Controlled Pilot Track: finish accepting T-005, then harden audit/UX/reporting through T-006–T-008, and only then run a pilot-readiness review before any deployment or master-merge decision.
```

## Immediate next decision

One Sponsor decision is needed now:

```text
Approve Controlled Pilot Track and authorize PM to prepare T-006 after T-005 acceptance.
```

If Sponsor wants a branch/deployment decision first, PM recommendation is to defer it until after T-005 acceptance and a pilot-readiness review, unless there is an external operational deadline.
