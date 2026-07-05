# Studio Suite Strategic Decision — Controlled Pilot Track

Date: 2026-07-05
Status: ACCEPTED
Project: Studio Suite
Authority: Sponsor
Decision source: Sponsor reply approving the PM recommendation
Related recommendation: `aios/strategy/2026-07-05-studio-suite-strategic-recommendation.md`

## Decision

Sponsor approves:

```text
Controlled Pilot Track
```

Sponsor also authorizes PM to prepare T-006 after T-005 acceptance:

```text
Authorize PM to prepare T-006 after T-005 acceptance.
```

## Accepted strategic direction

Studio Suite development proceeds as a controlled pilot track centered on the modern Salon Module / Legacy CAISSE transition.

This means:

1. Product development continues through bounded vertical slices.
2. Legacy CAISSE is treated as the transition surface toward a modern Salon Module, not as a goal to preserve WinDev architecture.
3. Product acceptance remains separate from deployment and branch-policy decisions.
4. Pilot safety hardening comes before production deployment or branch promotion.
5. Full WinDev/Bureau reconstruction, broad rewrite, and premature `master` merge remain out of scope.

## Approved candidate sequence

The strategic sequence accepted for planning purposes is:

| Step | Candidate | Purpose |
|---:|---|---|
| 0 | T-005 acceptance | Close correction/void slice. |
| 1 | T-006 — Correction reason / audit trail | Make void/correction auditable enough for pilot use. |
| 2 | T-007 — Operator UX hardening | Replace minimal operator controls with safer explicit actions. |
| 3 | T-008 — Daily close report export/print-lite | Give manager reviewable end-of-day evidence. |
| 4 | T-009 — Pilot readiness review | Decide whether branch is ready for staging/pilot/deployment policy. |

## Conditional authorization

PM is authorized to prepare T-006 only after T-005 is accepted by Sponsor.

Current boundary at time of this decision:

```text
T-005 implementation commit exists: 38183b9 impl(t005): protect legacy caisse fiche void flow
T-005 status: ready-for-review
T-005 acceptance: not yet recorded in this decision
```

Therefore this decision does not itself create the T-006 Objective/ticket package yet.

## Authority boundary

This decision does **not** authorize:

- production deployment;
- merge/promote to `master`;
- branch-policy change beyond continuing to use `feature/legacy-caisse-flow` as active integration branch;
- assigning Deployment Authority;
- full WinDev/Bureau reconstruction;
- broad UI redesign;
- fiscal printing;
- exploitation report suite;
- public booking changes;
- implementation of T-006 before T-005 acceptance.

## Consequence

The next PM action should be one of:

1. record T-005 acceptance if Sponsor explicitly accepts T-005;
2. if T-005 is accepted, prepare T-006 Objective/ticket/dispatch/flag;
3. otherwise keep T-006 preparation pending and continue review/decision on T-005.
