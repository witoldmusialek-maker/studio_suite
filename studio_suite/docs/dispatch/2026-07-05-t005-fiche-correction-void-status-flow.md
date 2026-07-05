# Dispatch — T-005 Fiche Correction / Void / Status Flow

You are implementing a bounded Studio Suite delivery task.

## Repository

`/home/witold/projects/projekt2_repo`

Current operational branch must remain:

```text
feature/legacy-caisse-flow
```

Do not merge to `master`. Do not deploy to production.

## Ticket

Read first:

```text
studio_suite/docs/tickets/005-fiche-correction-void-status-flow.md
aios/objectives/AIOS-OBJ-SS-005-legacy-caisse-fiche-correction.md
studio_suite/docs/tickets/003-legacy-caisse-minimal-flow.md
studio_suite/docs/tickets/004-cash-session-lifecycle-and-daily-summary.md
studio_suite/docs/RULES.md
studio_suite/docs/legacy-caisse-transition-plan.md
studio_suite/docs/AGENT_MAP.md
studio_suite/docs/AGENT_START.md
```

## Mission

Implement the smallest useful Legacy CAISSE correction/status slice:

```text
void/correct mistaken fiche → payment becomes non-counting → daily summary remains trustworthy → closed cash day is protected
```

## Hard Scope Guards

Do not touch public booking except to verify it remains separate.
Do not alter deployment scripts, nginx configs, secrets, or unrelated modules.
Do not add real client data or secrets.
Do not perform production deployment.
Do not merge/promote to `master`.
Do not broaden scope into full WinDev/Bureau reconstruction, fiscal printing, exploitation reports, or file database synchronization.

## TDD Requirement

Use strict test-first development for backend correction/status behavior:

1. Add failing test(s) for valid void, summary exclusion, duplicate void behavior, and closed-day protection.
2. Run targeted pytest and observe expected failure.
3. Implement minimal code to pass.
4. Re-run targeted tests and required checks.

Expected new test path:

```text
studio_suite/backend/tests/test_legacy_caisse_fiche_correction.py
```

## Expected Implementation Shape

Prefer extending existing:

- `void_fiche` in `legacy_caisse.py`;
- `Sale.status` and `Payment.status` semantics;
- T-004 daily summary filter behavior;
- `LegacyCaissePage.tsx` fiche list action.

Conservative default:

- voiding a fiche on an open/unclosed cash day is allowed;
- voiding a fiche after the cash session for that day is closed is blocked with a clear 409 unless an explicit correction path is introduced and tested;
- duplicate void should be predictable and documented, either idempotent or 409 conflict.

## Expected Evidence

Before finishing, provide:

1. Summary of changed files.
2. Chosen status-transition semantics.
3. Daily summary exclusion evidence.
4. Closed-day protection evidence.
5. Tenant/salon/module guard evidence.
6. Public/private separation evidence.
7. Validation commands and results.
8. Known limitations/deferred scope.

## Required Checks

At minimum:

```bash
git status --short
cd studio_suite/backend && .venv/bin/python -m pytest tests/test_legacy_caisse_minimal_flow.py tests/test_legacy_caisse_cash_session.py tests/test_legacy_caisse_fiche_correction.py -q
cd studio_suite/backend && .venv/bin/python -m compileall app
cd studio_suite/frontend && npm run build -- --outDir /tmp/studio-suite-vite-build --emptyOutDir
```

Runtime health when available:

```bash
curl -s -o /dev/null -w '%{http_code}\n' http://192.168.50.20:8003/health
curl -s -o /dev/null -w '%{http_code}\n' http://192.168.50.20:8004/health
curl -s -o /dev/null -w '%{http_code}\n' https://dev2.witold.ovh/health
```

## Handoff Artifacts

Create:

- `studio_suite/docs/handoffs/2026-07-05-t005-fiche-correction-void-status-flow.md`
- `studio_suite/docs/postmortems/2026-07-05-t005-fiche-correction-void-status-flow.md`

Do not claim done unless checks actually ran or blocker is explicit.
