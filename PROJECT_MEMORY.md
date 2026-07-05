# Studio Suite — Project Memory

Status: AIOS-onboarded project
AIOS onboarding state: Minimum Viable Understanding achieved
Delivery readiness: four bounded Legacy CAISSE deliveries accepted
Project Memory purpose: entry point, not archive
Last updated: 2026-07-05

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
- AIOS-OBJ-SS-001 accepted by Sponsor; PM verdict: `Not ready — further operational cleanup required`;
- AIOS-OBJ-SS-002 accepted by Sponsor; PM verdict: `Ready after Sponsor authority decision`;
- operational branch accepted for first feature/delivery Objective planning: `feature/legacy-caisse-flow`;
- merge to `master` deferred until after one successful delivery or separate branch-policy decision;
- first feature/delivery Objective approved: AIOS-OBJ-SS-003 — Legacy CAISSE Minimal Flow;
- T-003 accepted by Sponsor as first bounded Legacy CAISSE delivery slice;
- T-004 accepted by Sponsor as first usable Legacy CAISSE day-cycle slice;
- T-005 accepted by Sponsor as safe correction/void guard slice;
- Sponsor granted PM mandate to prepare strategic recommendations for further application development;
- strategic recommendation accepted by Sponsor: Controlled Pilot Track for Studio Suite / Legacy CAISSE;
- PM authorized to prepare T-006 after T-005 acceptance; T-006 preparation package created;
- PM authorized to plan, delegate, supervise, and accept implementation work within approved Objectives and existing AIOS governance;
- PM operational acceptance concludes implementation work within an approved Objective;
- Sponsor approval is required only where AIOS governance explicitly reserves authority to Sponsor;
- T-006 accepted by PM under delegated operational implementation authority as correction reason / audit trail slice;
- single controlled deployment to current development environment authorized by Sponsor under AIOS-OBJ-SS-001; authorization expires after completion;
- production deployment, merge to `master`, long-term Deployment Authority, and branch policy remain unresolved/separate decisions.

## 3. Current Active State

Resolved facts:

```text
Current local branch: feature/legacy-caisse-flow
Remote default branch: origin/master
Current dirty files: none
Last accepted delivery commits:
  - d715404 impl(t003): harden legacy caisse minimal flow
  - fdf9172 impl(t004): add legacy caisse cash day summary
  - 38183b9 impl(t005): protect legacy caisse fiche void flow
  - 0d04411 impl(t006): add legacy caisse correction audit trail
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

- whether to make `feature/legacy-caisse-flow` the official long-term branch for future AIOS work, merge it to `master`, or define another branch policy;
- long-term deployment policy after the one-time controlled development deployment;
- who owns long-term Deployment Authority.

## 4. Authority Snapshot

Default rule from AIOS Cross-Project Onboarding Practice:

> During project onboarding the Sponsor is the default Project Authority until another Project Authority is explicitly designated.

Current authority state:

```text
Project Authority: Sponsor
Acceptance Authority: Sponsor
Deployment Authority: UNRESOLVED long-term; PM has one-time Sponsor authorization for controlled development deployment only
AIOS PM role: onboarding, operational evolution management within approved Objectives, planning/delegation/supervision/operational acceptance of implementation work, Objective Proposal preparation, delivery review, recommendations for authority/strategy decisions
Implementation authority: bounded to approved Objectives under existing AIOS governance
Delegation authority: bounded to approved Objectives under existing AIOS governance
Delivery authority: T-003, T-004, T-005, and T-006 accepted; future delivery requires next Objective approval/preparation within accepted track
```

Sponsor decision update:

- evidence phase is complete;
- branch policy may remain unchanged until an Objective provides sufficient evidence for promotion or merge decision;
- first bounded delivery evidence exists: T-003 accepted as Legacy CAISSE minimal flow;
- second bounded delivery evidence exists: T-004 accepted as Legacy CAISSE daily cash-session flow;
- third bounded delivery evidence exists: T-005 accepted as Legacy CAISSE correction/void guard flow;
- fourth bounded delivery evidence exists: T-006 accepted as Legacy CAISSE correction reason / audit trail flow;
- strategic recommendation accepted by Sponsor: Controlled Pilot Track, with T-007 UX hardening / T-008 daily close report / T-009 pilot readiness review as candidate sequence;
- PM authorized to prepare T-006 after T-005 acceptance; condition satisfied and T-006 accepted;
- PM may plan, delegate, supervise, and accept implementation work within approved Objectives; PM operational acceptance concludes implementation work; Sponsor approval is required only where AIOS governance explicitly reserves authority to Sponsor.

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
2. Deployment Authority unresolved.
3. Tenant isolation and public/private split are critical and must not be weakened.
4. Privacy/security surface is significant: clients, appointments, billing, payments, SMS, tenant data.
5. Some documentation may still be stale relative to live runtime.

## 11. Unknown Facts

UNRESOLVED facts that require Sponsor or designated Project Authority before delivery:

- official branch policy for future work;
- whether/when accepted T-003 should be deployed beyond the current runtime baseline;
- explicit Project Authority beyond Sponsor default if Sponsor delegates it;
- Deployment Authority;
- execution of future Objectives beyond T-006 / preparation of T-007;
- production/pilot status of public booking, payments, billing, SMS, and broader legacy CAISSE.

## 12. PM Readiness

Current PM readiness:

| Capability | Status |
|---|---|
| Discuss project | YES |
| Evaluate Decision Proposals | YES, bounded by unresolved authority |
| Plan next candidate Objective | YES |
| Delegate implementation | YES, within approved Objectives under existing AIOS governance |
| Review/accept implementation | YES; PM operational acceptance concludes implementation work inside approved Objectives |
| Start next delivery | YES within approved/prepared Objectives; escalate only where AIOS governance reserves Sponsor authority |

## 13. Scope Guard

This Project Memory does not authorize work outside approved Objectives. Within approved Objectives, PM may manage operational evolution and conclude implementation work through operational acceptance under existing AIOS governance.

This Project Memory does not authorize:

- Objective creation;
- Value Delivery;
- implementation or delegation outside approved Objectives;
- deployment;
- accepting dirty worktree changes;
- making branch-policy decisions beyond recording operational evidence;
- changing governance;
- promoting Cross-Project Onboarding to AIOS Core.
