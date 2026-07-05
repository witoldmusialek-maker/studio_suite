# AIOS-OBJ-SS-002 Closeout — Normalize Studio Suite Operational Baseline

Date: 2026-07-04
Status: PM_RECOMMENDATION_ISSUED
Project: Studio Suite
Objective: AIOS-OBJ-SS-002 — Normalize Studio Suite Operational Baseline

## PM Verdict

```text
Ready after Sponsor authority decision
```

Studio Suite's operational baseline has been normalized enough to support a future first feature/delivery Objective, provided Sponsor accepts this cleanup package and makes the remaining authority decisions.

Feature delivery is still not authorized by this closeout.

## Summary of Changes

### Backend syntax blocker removed

Removed UTF-8 BOM from:

- `studio_suite/backend/app/api/v1/legacy_caisse.py`
- `studio_suite/backend/app/schemas/legacy_caisse.py`

### Smoke/auth baseline normalized

Updated:

- `studio_suite/scripts/smoke-test.ps1`

New behavior:

- supports non-secret health smoke via `-HealthOnly`;
- removes hard-coded `admin/password123` defaults;
- reads credentials from `STUDIO_SUITE_SMOKE_USERNAME` / `STUDIO_SUITE_SMOKE_PASSWORD` or explicit parameters;
- fails clearly when authenticated smoke lacks credentials or hits TOTP/auth requirements;
- does not commit secrets.

### Deployment references normalized

Updated operational references toward current evidence-backed target:

```text
192.168.50.20
feature/legacy-caisse-flow
```

Touched areas:

- root `README.md`;
- `deploy.ps1`;
- `studio_suite/docs/AGENT_REMOTE_SETUP.md`;
- `studio_suite/docs/AGENT_MAP.md`;
- `studio_suite/docs/AGENT_START.md`;
- `studio_suite/nginx/gateway-dev2.witold.ovh.conf`;
- `studio_suite/nginx/gateway-dev3.witold.ovh.conf`;
- `studio_suite/scripts/deploy-dev1.ps1`;
- `studio_suite/scripts/deploy-dev2.ps1`;
- `studio_suite/scripts/sync-to-dev.ps1`;
- `studio_suite/scripts/sync-from-dev.ps1`.

Historical `dev1` wording remains only in the root README as explicit history:

```text
historyczny host dev1
```

## Acceptance Criteria Results

### AC-1 — Backend syntax blocker removed

Result: PASS

```text
checked_py_files=50
backend_ast_syntax=PASS
```

### AC-2 — Smoke/auth baseline normalized

Result: PASS with environment limitation

Implemented script support for:

```powershell
studio_suite/scripts/smoke-test.ps1 -BaseUrl http://192.168.50.20:8003 -HealthOnly
```

Authenticated smoke now requires approved credentials and does not rely on stale committed defaults.

Runtime note:

```text
pwsh not installed in current Linux shell, so the PowerShell smoke script was not executed directly here.
Equivalent curl health checks passed.
```

### AC-3 — Deployment references normalized or classified

Result: PASS

Stale direct references to `192.168.200.116` were replaced in operational docs/scripts/nginx configs. `dev1` was replaced in active operational instructions and kept only as historical context in README.

### AC-4 — Dirty deployment-script changes resolved within Objective scope

Result: PASS

Existing dirty deployment-script changes are now part of the cleanup package and should be accepted with this Objective if Sponsor accepts the closeout.

### AC-5 — Baseline verification rerun

Result: PASS for available gates

Frontend build:

```text
npm run build -- --outDir /tmp/studio-suite-vite-build --emptyOutDir
✓ built in 30.23s
```

Health checks:

```text
http://192.168.50.20:8003/health -> 200 {"status":"ok","version":"v1.0.0-beta.2026-05-15.T02"}
http://192.168.50.20:8004/health -> 200 {"status":"ok","version":"v1.0.0-beta.2026-03-14.T30"}
https://dev2.witold.ovh/health -> 200 {"status":"ok","version":"v1.0.0-beta.2026-05-15.T02"}
```

Stale reference scan:

```text
No active operational references found to:
- 192.168.200.116
- git push origin master
- git checkout master
- git pull origin master

Remaining dev1 text is historical context only.
```

### AC-6 — Operational readiness verdict issued

Result:

```text
Ready after Sponsor authority decision
```

### AC-7 — Authority boundary preserved

Preserved:

```text
Project Authority: Sponsor
Acceptance Authority: Sponsor
Deployment Authority: unresolved
Feature delivery: not performed
Deployment: not performed
Merge to master: not performed
Delegation: not performed
```

## Branch Policy Recommendation

Recommended branch policy:

```text
Accept feature/legacy-caisse-flow as the operational branch for the next delivery planning step.
Defer merge/promote-to-master until after Sponsor accepts this cleanup and decides whether master should resume canonical/default role.
```

Rationale:

- current runtime and cleanup are on `feature/legacy-caisse-flow`;
- `master` remains stale relative to current operational baseline;
- merge/promotion should be an explicit authority decision, not an incidental cleanup side-effect.

## Deployment Target Recommendation

Recommended deployment target:

```text
192.168.50.20
```

Rationale:

- live runtime is healthy on `192.168.50.20`;
- compose publishes services on `192.168.50.20`;
- docs/scripts/nginx configs have now been normalized to that target.

## PM Recommendation

Sponsor should accept AIOS-OBJ-SS-002 and then decide one of two paths:

### Recommended path

```text
Accept cleanup package.
Keep feature/legacy-caisse-flow as operational branch for first feature/delivery Objective planning.
Defer merge to master until after one successful delivery or separate branch-policy decision.
```

### Alternative path

```text
Accept cleanup package.
Immediately authorize a branch-policy Objective to merge/promote operational baseline to master before any feature delivery.
```

PM recommends the first path because it avoids mixing operational cleanup, branch policy, and feature delivery.

## Final State

```text
Operational cleanup complete: YES
Backend syntax blocker removed: YES
Frontend build passes: YES
Runtime health passes: YES
Smoke/auth baseline normalized: YES
Deployment docs/scripts normalized: YES
Ready for first feature/delivery Objective: after Sponsor acceptance/authority decision
```
