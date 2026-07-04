# AIOS-OBJ-SS-001 Closeout — Studio Suite Operational Baseline

Date: 2026-07-04
Status: PM_RECOMMENDATION_ISSUED
Project: Studio Suite
Objective: Establish Studio Suite Operational Baseline

## PM Verdict

```text
Not ready — further operational cleanup required
```

Studio Suite has a clear live operational baseline, but it is not yet ready for the first feature/delivery Objective.

The baseline is understandable and reachable, but predictable operation is blocked by:

- stale deployment documentation and scripts;
- dirty deployment-script changes not yet accepted;
- backend syntax check failure caused by BOM in legacy CAISSE Python files;
- smoke test credentials in the documented script no longer matching the live auth state;
- branch policy still requiring Sponsor/Authority decision after cleanup evidence.

## AC-1 — Current runtime baseline confirmed

Evidence collected:

```text
Current branch: feature/legacy-caisse-flow
Remote default: origin/master
HEAD: 1ff06d2 docs(aios): approve Studio Suite operational baseline objective
master: cf0e241 Implement tenant license billing with email reminders and SMTP config
master is ancestor of HEAD: yes
master...HEAD: 0 behind / 11 ahead
Dirty files:
  M deploy.ps1
  M studio_suite/scripts/deploy-dev2.ps1
```

Docker compose state:

```text
studio_suite-backend-1           running healthy   192.168.50.20:8003->8000
studio_suite-backend_public-1    running healthy   192.168.50.20:8004->8000
studio_suite-db-1                running healthy
studio_suite-frontend-1          running           192.168.50.20:8082->80
studio_suite-frontend_public-1   running           192.168.50.20:8084->80
```

Health checks:

```text
http://192.168.50.20:8003/health -> 200
{"status":"ok","version":"v1.0.0-beta.2026-05-15.T02"}

http://192.168.50.20:8004/health -> 200
{"status":"ok","version":"v1.0.0-beta.2026-03-14.T30"}

http://192.168.50.20:8082 -> 200
http://192.168.50.20:8084 -> 200

https://dev2.witold.ovh/health -> 200
{"status":"ok","version":"v1.0.0-beta.2026-05-15.T02"}
```

Assessment:

- Active runtime target is `192.168.50.20`.
- `feature/legacy-caisse-flow` is the operational branch for the live baseline.
- `master` remains remote default but is stale for current runtime shape.

## AC-2 — Deployment scripts assessed

Dirty changes:

```text
deploy.ps1:
  192.168.200.116 -> 192.168.50.20

studio_suite/scripts/deploy-dev2.ps1:
  DirectApiBaseUrl:
  http://192.168.200.116:8003 -> http://192.168.50.20:8003
```

Assessment:

- The direction of the dirty changes is correct: `192.168.50.20` matches the live runtime.
- The scripts are not yet predictable enough to accept as-is.
- They still contain stale assumptions/names such as `dev1` and `master`.
- There are 39 stale references across README/docs/scripts/nginx involving `192.168.200.116`, `dev1`, or `master`.
- Repo gateway configs still reference `192.168.200.116`, while live public health succeeds.

Recommendation:

- Do not accept the dirty deploy-script changes as isolated final state.
- Create a small operational cleanup Objective or task to normalize deployment docs/scripts around `192.168.50.20` and current branch policy.

## AC-3 — Branch policy recommendation prepared

Recommendation:

```text
Continue using feature/legacy-caisse-flow as the operational branch for now.
Do not merge to master until operational cleanup is complete and verified.
After cleanup, promote/merge to master if Sponsor wants master to resume canonical/default role.
```

Rationale:

- Live runtime aligns with `feature/legacy-caisse-flow`.
- `master` is an ancestor and is stale.
- Premature merge would preserve stale deployment assumptions unless cleanup is done first.

## AC-4 — Verification path defined

Minimum verification path for future delivery Objectives:

1. Git state check:

```bash
git branch --show-current
git status --short
git log -1 --format='%H %ci %s'
```

2. Backend syntax check without writing pyc:

```bash
python3 - <<'PY'
import ast, pathlib, sys
root = pathlib.Path('studio_suite/backend/app')
errors = []
for p in sorted(root.rglob('*.py')):
    try:
        ast.parse(p.read_text(encoding='utf-8'), filename=str(p))
    except Exception as e:
        errors.append((str(p), repr(e)))
if errors:
    for path, err in errors:
        print(f'ERROR {path}: {err}')
    sys.exit(1)
print('backend_ast_syntax=PASS')
PY
```

3. Frontend build without modifying repo:

```bash
cd studio_suite/frontend
npm run build -- --outDir /tmp/studio-suite-vite-build --emptyOutDir
```

4. Runtime health:

```bash
curl -sS --max-time 5 http://192.168.50.20:8003/health
curl -sS --max-time 5 http://192.168.50.20:8004/health
curl -sS --max-time 5 https://dev2.witold.ovh/health
```

5. Smoke/auth path:

- update smoke credentials or authentication mode before treating smoke as a gate;
- current documented default credentials are stale.

## AC-5 — Operational readiness verdict issued

Verdict:

```text
Not ready — further operational cleanup required
```

Reason:

- Runtime is healthy.
- Frontend build passes to temporary output.
- Backend syntax check fails on BOM in legacy CAISSE Python files.
- Smoke login using documented/default credentials fails.
- Deployment docs/scripts are stale and inconsistent.

## AC-6 — Authority boundary preserved

Preserved:

```text
Project Authority: Sponsor
Acceptance Authority: Sponsor
Deployment Authority: unresolved
Feature delivery: not authorized
Deployment: not performed
Delegation: not performed
```

No branch policy was accepted by PM. No dirty deploy-script changes were committed.

## Verification Results

### Backend AST syntax check

Result: FAIL

```text
checked_py_files=50
ERROR studio_suite/backend/app/api/v1/legacy_caisse.py: SyntaxError invalid non-printable character U+FEFF
ERROR studio_suite/backend/app/schemas/legacy_caisse.py: SyntaxError invalid non-printable character U+FEFF
```

### Frontend build

Result: PASS

```text
npm run build -- --outDir /tmp/studio-suite-vite-build --emptyOutDir
✓ 12375 modules transformed
✓ built in 30.98s
```

Vite warning: some chunks exceed 500 kB. This is not a blocker for operational readiness.

### Smoke/auth check

Result: FAIL as documented gate

```text
admin/password123 -> 401 Incorrect username or password
superadmin/default -> 401 TOTP_REQUIRED
```

Assessment:

- The documented smoke credentials are stale for current runtime.
- Superadmin requires TOTP, so current auth state is stronger than the simple smoke script assumes.
- Smoke gate must be updated before future delivery can rely on it.

## PM Recommendation

Recommended next Objective / authority action:

```text
Approve a bounded Operational Cleanup Objective before feature delivery.
```

Suggested scope:

1. Remove BOM from the two legacy CAISSE Python files.
2. Update smoke/auth procedure to match current TOTP/auth reality without embedding secrets.
3. Normalize deployment docs/scripts to current target `192.168.50.20`.
4. Preserve `feature/legacy-caisse-flow` as operational branch during cleanup.
5. Re-run baseline verification.
6. Then decide whether to promote/merge to `master`.

Do not start feature delivery before this cleanup passes.

## Final State

```text
Objective evidence complete: YES
Operational baseline understood: YES
Operational readiness achieved: NO
Ready for first delivery Objective: NO
Ready for cleanup Objective: YES
```
