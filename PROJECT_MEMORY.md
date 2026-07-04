# Studio Suite — Project Memory

Status: AIOS-onboarded project
AIOS onboarding state: Minimum Viable Understanding achieved
Delivery readiness: not yet delivery-ready
Project Memory purpose: entry point, not archive
Last updated: 2026-07-04

## 1. Project Identity

Studio Suite is a salon operations / service-business management system.

Primary purpose:

> Manage salon operations: clients, appointments, services, bundles, inventory, payments, reports, public booking, tenants/licensing, and SMS communication.

Primary domain:

```text
salon operations / service-business management
```

Primary users visible from documentation and UI structure:

- admin / main manager;
- salon manager;
- receptionist;
- public booking customer;
- operator/developer responsible for runtime/deploy;
- Android SMS bridge as technical sending channel.

UNRESOLVED:

- which product roles are actively used in production vs model/planned roles.

## 2. AIOS Program Relationship

Studio Suite is the first project onboarded after validation of the AIOS Cross-Project Onboarding Program Practice.

Program classification:

```text
AIOS Program project
Cross-Project Onboarding validation vehicle
Onboarded, not delivery-ready
```

Current AIOS status:

- Minimum Viable Understanding: achieved;
- onboarding evidence boundary: reached;
- further evidence collection is not expected to materially improve readiness without authority decisions;
- Project Memory creation authorized by Sponsor and completed;
- AIOS-OBJ-SS-001 executed; PM verdict: `Not ready — further operational cleanup required`;
- delivery not authorized beyond operational-readiness assessment;
- first feature/delivery Objective not authorized;
- recommended next step: bounded Operational Cleanup Objective before feature delivery.

## 3. Current Active State

Resolved facts:

```text
Current local branch: feature/legacy-caisse-flow
Remote default branch: origin/master
Current dirty files:
  - deploy.ps1
  - studio_suite/scripts/deploy-dev2.ps1
Dirty change meaning:
  - deployment host references changed from 192.168.200.116 to 192.168.50.20
Live direct runtime:
  - http://192.168.50.20:8003/health -> 200
  - http://192.168.50.20:8004/health -> 200
  - http://192.168.50.20:8082 -> 200
  - http://192.168.50.20:8084 -> 200
Public health:
  - https://dev2.witold.ovh/health -> 200
Local compose state:
  - db running healthy
  - backend running healthy
  - backend_public running healthy
  - frontend running
  - frontend_public running
```

Architecture Discovery update:

- operational canonical branch for the current runtime is `feature/legacy-caisse-flow`;
- `master` remains the remote default branch but is stale for the current runtime shape;
- `master` is an ancestor of `feature/legacy-caisse-flow`; the feature branch is ahead and contains the legacy CAISSE/runtime binding changes;
- active deployment target is `192.168.50.20` for the live compose runtime;
- `192.168.200.116` references in docs/gateway files are historical/stale unless a future authority decision revives them;
- live containers were built from `/home/witold/projects/projekt2_repo/studio_suite/docker-compose.yml` and publish on `192.168.50.20`;
- live public health at `https://dev2.witold.ovh/health` works, but repo gateway config is not reliable as current gateway truth.

Deployment script assessment:

- dirty deploy-script changes from `192.168.200.116` to `192.168.50.20` align with the live runtime target;
- scripts still contain stale naming/assumptions (`dev1`, `master`) and should not be treated as authoritative deployment policy without cleanup;
- deployment scripts are operational evidence, not authority.

Authority decisions still required:

- whether to make `feature/legacy-caisse-flow` the official branch for future AIOS work, merge it to `master`, or define another branch policy;
- whether to commit/accept the dirty deployment-script changes;
- who owns Deployment Authority and Acceptance Authority.

## 4. Authority Snapshot

Default rule from AIOS Cross-Project Onboarding Practice:

> During project onboarding the Sponsor is the default Project Authority until another Project Authority is explicitly designated.

Current authority state:

```text
Project Authority: Sponsor
Acceptance Authority: Sponsor
Deployment Authority: UNRESOLVED until operational responsibilities are formally assigned
AIOS PM role: onboarding, recommendation, Objective Proposal preparation
Implementation authority: not authorized
Delegation authority: not authorized
Delivery authority: not authorized until Objective approval
```

Sponsor decision update:

- evidence phase is complete;
- branch policy may remain unchanged until an Objective provides sufficient evidence for promotion or merge decision;
- PM is authorized to prepare the first Objective Proposal focused on restoring predictable operational readiness.

PM must not infer authority from:

- branch names;
- commit history;
- product roles;
- deployment scripts;
- runtime health;
- last committer;
- repository documentation.

## 5. Architecture Snapshot

Main building blocks:

```text
studio_suite/
  backend/   FastAPI + SQLAlchemy
  frontend/  React + Vite + MUI
  android/   Android SMS bridge
  docs/      project documentation
  scripts/   deploy/smoke/setup scripts
  nginx/     gateway/dev nginx configs
  docker-compose.yml
```

Runtime services from compose:

| Service | Purpose |
|---|---|
| db | PostgreSQL 15 |
| backend | operational API, port 8003 |
| frontend | operational panel, port 8082 |
| backend_public | public booking API, port 8004 |
| frontend_public | public booking frontend, port 8084 |

Important architectural boundary:

```text
operational panel/API != public booking surface
```

Public API entrypoint is separated through `app.public_main:app`, while operational API uses `app.main:app`.

## 6. Business Domain Map

Known active/implemented areas from README, docs, route registration, and UI routing:

- auth and roles;
- salons, staff, products/resources;
- clients and appointments;
- service catalog and bundles;
- reports and legacy reports;
- inventory and stocktake;
- payments/sales;
- tenants and licenses;
- public booking;
- Android/local SMS bridge;
- legacy CAISSE transition flow.

Legacy architecture context:

- the project contains legacy salon-system material from a WinDev-era application as reverse-engineering evidence;
- legacy data/source material is present under `studio_suite/backend/tmp/legacy_05` and `studio_suite/backend/tmp/legacy_12` as `.FIC` / `.NDX` files;
- import/reverse-engineering tools exist under `studio_suite/tools/legacy_import`;
- the target direction is not to keep WinDev as runtime, but to build a server-side Salon Module with equivalent business capabilities;
- `legacy_caisse` is therefore an active architectural transition area, not merely historical documentation.

UNRESOLVED:

- which modules are production-active, pilot-active, or only technically present;
- current product/delivery priority.

## 7. Operational Boundaries

Critical boundaries from project rules and onboarding evidence:

- tenant isolation is the primary architectural rule;
- operational endpoints must be tenant-aware;
- public booking remains separate from operational panel/API;
- operational API/panel target access is intended to be controlled, with VPN/WireGuard mentioned in docs;
- module licensing must block API and hide UI when inactive;
- secrets must come from environment, not repo;
- privacy/RODO concerns apply to clients, appointments, billing, SMS, audit logs, and retention.

## 8. Verification Path

Known verification sources:

- `studio_suite/TESTING.md`;
- `studio_suite/QUICK_START.md`;
- `studio_suite/docs/AGENT_REMOTE_SETUP.md`;
- `studio_suite/scripts/smoke-test.ps1`;
- `studio_suite/docker-compose.yml`.

Known checks:

```text
frontend build: cd studio_suite/frontend && npm run build
backend compile: cd studio_suite/backend && python -m compileall app
runtime health: /health on backend/backend_public
smoke direct/public: studio_suite/scripts/smoke-test.ps1
manual checklist: login, resources, legacy catalog, reports
```

UNRESOLVED:

- mandatory test policy per change type;
- required acceptance gates for delivery;
- whether current smoke credentials/environment are authoritative.

## 9. Source of Truth Index

| Topic | Source of Truth / Pointer | Status |
|---|---|---|
| Project purpose | `README.md`, `studio_suite/README.md` | usable |
| Agent/project orientation | `studio_suite/docs/AGENT_MAP.md`, `studio_suite/docs/AGENT_START.md` | usable |
| Architecture/security rules | `studio_suite/docs/RULES.md` | usable |
| Runtime shape | `studio_suite/docker-compose.yml` | usable |
| Testing/smoke | `studio_suite/TESTING.md`, `studio_suite/scripts/smoke-test.ps1` | usable |
| Remote/dev workflow | `studio_suite/docs/AGENT_REMOTE_SETUP.md` | stale for current target; useful historically |
| Deployment scripts | `studio_suite/scripts/deploy-dev2.ps1`, `deploy.ps1` | dirty; directionally aligned to `192.168.50.20` but not policy |
| Gateway config | `studio_suite/nginx/*.conf` | stale vs live public health unless verified on gateway |
| Legacy CAISSE scope | `studio_suite/docs/legacy-caisse-transition-plan.md` | usable |
| SMS bridge | `studio_suite/android/sms_bridge/README.md` | usable |
| Authority | Sponsor / explicit Program decision | unresolved beyond Sponsor default |

## 10. Risk Notes

High-priority risks before delivery:

1. Branch policy ambiguity: operational runtime aligns with `feature/legacy-caisse-flow`, while remote default remains `master`.
2. Stale deployment documentation/config: live target is `192.168.50.20`, while historical `192.168.200.116` references remain.
3. Dirty deploy scripts not accepted by authority.
4. Project/Acceptance/Deployment Authority unresolved.
5. Tenant isolation and public/private split are critical and must not be weakened.
6. Privacy/security surface is significant: clients, appointments, billing, payments, SMS, tenant data.
7. Some documentation is stale relative to live runtime.

## 11. Unknown Facts

UNRESOLVED facts that require Sponsor or designated Project Authority before delivery:

- official branch policy for future work;
- whether `192.168.50.20` is formally accepted as deployment target;
- acceptance of dirty deploy script changes;
- explicit Project Authority;
- Acceptance Authority;
- Deployment Authority;
- permission for first Objective;
- permission for delivery/delegation;
- current product/delivery priority after legacy CAISSE work;
- production/pilot status of public booking, payments, billing, SMS, and legacy CAISSE.

## 12. PM Readiness

Current PM readiness:

| Capability | Status |
|---|---|
| Discuss project | YES |
| Evaluate Decision Proposals | YES, bounded by unresolved authority |
| Plan candidate Objective | PARTIAL |
| Delegate implementation | NO |
| Review implementation | PARTIAL / no final acceptance |
| Start delivery | NO |

## 13. Scope Guard

This Project Memory does not authorize:

- Objective creation;
- Value Delivery;
- implementation;
- delegation;
- deployment;
- accepting dirty worktree changes;
- making branch-policy decisions beyond recording operational evidence;
- changing governance;
- promoting Cross-Project Onboarding to AIOS Core.
