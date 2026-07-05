# Dispatch — T-004 Cash Session Lifecycle and Daily Summary

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
studio_suite/docs/tickets/004-cash-session-lifecycle-and-daily-summary.md
aios/objectives/AIOS-OBJ-SS-004-legacy-caisse-daily-cash-session.md
studio_suite/docs/RULES.md
studio_suite/docs/legacy-caisse-transition-plan.md
studio_suite/docs/AGENT_MAP.md
studio_suite/docs/AGENT_START.md
studio_suite/docs/tickets/003-legacy-caisse-minimal-flow.md
```

## Mission

Implement the smallest useful Legacy CAISSE day-cycle slice:

```text
open cash session → create/use fiches/payments → record expenses/presence → close cash session → review daily summary
```

## Hard Scope Guards

Do not touch public booking except to verify it remains separate.
Do not alter deployment scripts, nginx configs, secrets, or unrelated modules.
Do not add real client data or secrets.
Do not perform production deployment.
Do not merge/promote to `master`.
Do not broaden scope into full WinDev/Bureau reconstruction, fiscal printing, exploitation reports, or file database synchronization.

## TDD Requirement

Use strict test-first development for backend lifecycle/summary behavior:

1. Add failing test(s) for cash session lifecycle and daily summary.
2. Run targeted pytest and observe the expected failure.
3. Implement minimal code to pass.
4. Re-run targeted tests and then required checks.

Expected new test path:

```text
studio_suite/backend/tests/test_legacy_caisse_cash_session.py
```

## Expected Implementation Shape

Prefer extending existing:

- `CashierCashSession`;
- `CashierExpense`;
- `Sale`, `SaleLine`;
- `Payment`, `PaymentAllocation`;
- `legacy_caisse.py` endpoints;
- `LegacyCaissePage.tsx` UI.

Daily summary should include at least:

- opening cash;
- service gross;
- retail/product gross;
- discount total;
- payments by method;
- cash payments;
- expenses total;
- expected cash;
- closing cash;
- cash difference.

## Expected Evidence

Before finishing, provide:

1. Summary of changed files.
2. Explanation of lifecycle rules.
3. Summary calculation definition.
4. Tenant/salon/module guard evidence.
5. Public/private separation evidence.
6. Validation commands and results.
7. Known limitations/deferred scope.

## Required Checks

At minimum:

```bash
git status --short
cd studio_suite/backend && .venv/bin/python -m pytest tests/test_legacy_caisse_minimal_flow.py tests/test_legacy_caisse_cash_session.py -q
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

- `studio_suite/docs/handoffs/2026-07-05-t004-cash-session-lifecycle-and-daily-summary.md`
- `studio_suite/docs/postmortems/2026-07-05-t004-cash-session-lifecycle-and-daily-summary.md`

Do not claim done unless checks actually ran or blocker is explicit.
