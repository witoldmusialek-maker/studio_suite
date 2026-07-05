# AIOS-OBJ-SS-003 Acceptance — Legacy CAISSE Minimal Flow

Date: 2026-07-05
Status: ACCEPTED
Project: Studio Suite
Objective: AIOS-OBJ-SS-003 — Legacy CAISSE Minimal Flow
Ticket: T-003 — Legacy CAISSE Minimal Flow
Authority: Sponsor

## Sponsor Decision

Sponsor accepts the PM recommendation for T-003.

Accepted PM recommendation:

```text
Accept T-003 as the first bounded Legacy CAISSE delivery slice.
```

## Accepted Execution Package

Sponsor accepts the committed execution package:

```text
d715404 impl(t003): harden legacy caisse minimal flow
```

Accepted changed files:

```text
studio_suite/backend/app/api/v1/legacy_caisse.py
studio_suite/backend/tests/test_legacy_caisse_minimal_flow.py
studio_suite/docs/flags/2026-07-05-t003-legacy-caisse-minimal-flow.json
studio_suite/docs/handoffs/2026-07-05-t003-legacy-caisse-minimal-flow.md
studio_suite/docs/postmortems/2026-07-05-t003-legacy-caisse-minimal-flow.md
studio_suite/docs/tickets/003-legacy-caisse-minimal-flow.md
```

## Accepted Result

T-003 is accepted as a minimal backend-verified Legacy CAISSE cashier slice.

Accepted capabilities:

- minimal cashier fiche/sale creation path is preserved;
- current-month fiche listing path is preserved;
- sale/payment persistence path is covered by focused tests;
- staff from another salon is rejected before sale persistence;
- inactive/missing service is rejected before sale persistence;
- product lines require active salon product availability;
- bundle lines require active bundle availability;
- `LEGACY_CAISSE` module/license boundary remains enforced through router dependency;
- public booking surface was not changed.

## Accepted Verification Evidence

```text
backend targeted pytest: PASS — 3 passed, 7 warnings
backend compileall: PASS
frontend build: PASS — built in 26.46s
runtime health: PASS
  http://192.168.50.20:8003/health -> 200
  http://192.168.50.20:8004/health -> 200
  https://dev2.witold.ovh/health -> 200
git working tree after execution: clean
```

Warnings are accepted as non-blocking existing technical warnings:

- SQLAlchemy `declarative_base()` deprecation;
- passlib `crypt` deprecation;
- Pydantic class-based config deprecations;
- Vite CJS API and chunk-size warnings.

## Authority Boundary

This acceptance does not authorize by itself:

- production deployment;
- merge/promote to `master`;
- assigning Deployment Authority;
- broad Legacy CAISSE / WinDev / Bureau reconstruction;
- public booking changes;
- AIOS governance changes.

Project Authority: Sponsor
Acceptance Authority: Sponsor
Deployment Authority: unresolved
Operational branch remains: `feature/legacy-caisse-flow`

## Follow-up Recommendation

The next project decision should be one of:

1. define the next bounded Legacy CAISSE slice; or
2. make a separate branch/deployment policy decision after this successful delivery evidence.

PM recommendation: choose the next bounded product slice first; defer merge/promote-to-master until branch policy is explicitly useful.
