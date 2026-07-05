# Dispatch — T-006 Correction Reason / Audit Trail

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
studio_suite/docs/tickets/006-correction-reason-audit-trail.md
aios/objectives/AIOS-OBJ-SS-006-correction-reason-audit-trail.md
aios/objectives/AIOS-OBJ-SS-005-acceptance.md
studio_suite/docs/tickets/005-fiche-correction-void-status-flow.md
studio_suite/docs/tickets/004-cash-session-lifecycle-and-daily-summary.md
studio_suite/docs/tickets/003-legacy-caisse-minimal-flow.md
studio_suite/docs/RULES.md
studio_suite/docs/legacy-caisse-transition-plan.md
studio_suite/docs/AGENT_MAP.md
studio_suite/docs/AGENT_START.md
```

## Mission

Implement the smallest useful Legacy CAISSE audit slice:

```text
void/correct fiche → operator provides reason → audit record persists who/when/why → manager can read history
```

## Hard Scope Guards

Do not touch public booking except to verify it remains separate.
Do not alter deployment scripts, nginx configs, secrets, or unrelated modules.
Do not add real client data or secrets.
Do not perform production deployment.
Do not merge/promote to `master`.
Do not broaden scope into full WinDev/Bureau reconstruction, fiscal printing, exploitation reports, or file database synchronization.
Do not implement a full accounting journal.

## TDD Requirement

Use strict test-first development for backend audit behavior:

1. Add failing test(s) for void reason persistence, audit read path, closed-day no-audit-on-failure, and regression with daily summary exclusion.
2. Run targeted pytest and observe expected failure.
3. Implement minimal code to pass.
4. Re-run targeted tests and required checks.

Expected new test path:

```text
studio_suite/backend/tests/test_legacy_caisse_correction_audit.py
```

## Expected Implementation Shape

Prefer:

- a small explicit audit/correction model if no existing audit model fits;
- extending `void_fiche` to accept a reason payload while keeping compatibility where necessary;
- preserving T-005 closed-day guard before creating success audit records;
- adding a minimal `GET` read path for sale/fiche audit history;
- adding a small reason modal/prompt/action in `LegacyCaissePage.tsx`.

Conservative default:

- successful void requires a non-empty reason;
- duplicate void remains predictable and should not create misleading duplicate audit records unless explicitly modeled as a read action;
- failed closed-day void should not create a success audit record;
- audit is operational evidence, not fiscal/accounting journal.

## Expected Evidence

Before finishing, provide:

1. Summary of changed files.
2. Audit model/schema shape.
3. API semantics for reason and history read.
4. UI behavior.
5. Closed-day protection evidence.
6. Daily summary regression evidence.
7. Tenant/salon/module guard evidence.
8. Public/private separation evidence.
9. Validation commands and results.
10. Known limitations/deferred scope.

## Required Checks

At minimum:

```bash
git status --short
cd studio_suite/backend && .venv/bin/python -m pytest tests/test_legacy_caisse_minimal_flow.py tests/test_legacy_caisse_cash_session.py tests/test_legacy_caisse_fiche_correction.py tests/test_legacy_caisse_correction_audit.py -q
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

- `studio_suite/docs/handoffs/2026-07-05-t006-correction-reason-audit-trail.md`
- `studio_suite/docs/postmortems/2026-07-05-t006-correction-reason-audit-trail.md`

Do not claim done unless checks actually ran or blocker is explicit.
