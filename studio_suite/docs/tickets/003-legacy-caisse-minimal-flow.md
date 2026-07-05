# T-003 — Legacy CAISSE Minimal Flow

Status: ready-for-implementation
Project Objective: AIOS-OBJ-SS-003 — Legacy CAISSE Minimal Flow
Authority: Sponsor
Branch: `feature/legacy-caisse-flow`

## Goal

Deliver the first minimal end-to-end Legacy CAISSE cashier flow in Studio Suite's operational surface.

The flow should prove that a salon operator can create a basic cashier fiche/sale using the modern tenant/salon data model, then see it in the current-month fiche list.

## Scope

Implement the smallest useful slice covering:

1. Operational UI/API path for a Legacy CAISSE cashier fiche.
2. Tenant-scoped salon context.
3. At least one sale line from an existing service/product/bundle concept where available.
4. Payment capture using existing payment/sale model where available.
5. Current-month fiche list for the salon.
6. Guards for tenant isolation, salon access, and `LEGACY_CAISSE` module/license where currently supported.

Prefer integrating with existing models/endpoints/components over creating parallel duplicate domain concepts.

## Scope Paths

Primary candidate areas:

- `studio_suite/backend/app/api/v1/legacy_caisse.py`
- `studio_suite/backend/app/schemas/legacy_caisse.py`
- `studio_suite/backend/app/models/`
- `studio_suite/backend/app/services/` if existing service patterns require it
- `studio_suite/frontend/src/` Legacy CAISSE route/components/API client areas
- `studio_suite/docs/legacy-caisse-transition-plan.md` only for narrow status notes if needed

## Forbidden / Guarded Paths

Do not modify unless explicitly justified in handoff:

- `studio_suite/backend/app/public_main.py`
- `studio_suite/backend/app/api/v1/public_*`
- `studio_suite/frontend_public/` if present
- deployment scripts
- nginx/gateway configs
- secrets/env files
- unrelated auth, reporting, inventory, SMS, or public booking modules

## Acceptance Criteria

1. Minimal cashier fiche can be created through the operational surface/API.
2. Created fiche/sale is persisted tenant-safely.
3. Current-month fiche list returns the created item for the same salon/tenant.
4. Unauthorized cross-tenant/salon access is blocked by existing or added checks.
5. `LEGACY_CAISSE` module/license behavior is enforced or explicitly documented as a gap.
6. Public booking surface remains untouched and does not expose Legacy CAISSE.
7. Tests/checks pass and are recorded.

## Required Checks

Run and report:

```bash
git status --short
cd studio_suite/backend && python -m compileall app
# plus targeted pytest(s) for the changed backend path, if test framework is available
cd studio_suite/frontend && npm run build -- --outDir /tmp/studio-suite-vite-build --emptyOutDir
```

Runtime health to verify after implementation if environment is available:

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://192.168.50.20:8003/health
curl -s -o /dev/null -w '%{http_code}\n' http://192.168.50.20:8004/health
curl -s -o /dev/null -w '%{http_code}\n' https://dev2.witold.ovh/health
```

## Deliverables

- Code changes for the minimal flow.
- Tests or explicit test-gap explanation.
- Handoff under `studio_suite/docs/handoffs/`.
- Postmortem under `studio_suite/docs/postmortems/` if implementation is delegated to a worker.

## Out of Scope

- full WinDev/Bureau reconstruction;
- WDD/FIC/NDX runtime checks;
- CAISSE-to-Bureau transfer;
- exploitation reports;
- file database synchronization;
- production deployment;
- merge to `master`;
- broad domain rewrite.
