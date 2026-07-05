# Dispatch — T-003 Legacy CAISSE Minimal Flow

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
studio_suite/docs/tickets/003-legacy-caisse-minimal-flow.md
aios/objectives/AIOS-OBJ-SS-003-legacy-caisse-minimal-flow.md
studio_suite/docs/RULES.md
studio_suite/docs/legacy-caisse-transition-plan.md
studio_suite/docs/AGENT_MAP.md
studio_suite/docs/AGENT_START.md
```

## Mission

Implement the smallest useful end-to-end Legacy CAISSE cashier flow:

- create a minimal cashier fiche/sale in the operational surface/API;
- persist it tenant-safely;
- list current-month fiches for the same salon/tenant;
- preserve module/license, salon access, tenant isolation, and public/private boundaries.

## Hard Scope Guards

Do not touch public booking except to verify it remains separate.
Do not alter deployment scripts, nginx configs, secrets, or unrelated modules.
Do not add real client data or secrets.
Do not perform production deployment.
Do not merge/promote to `master`.

## Expected Evidence

Before finishing, provide:

1. Summary of changed files.
2. Explanation of how the minimal flow works.
3. Tenant/salon/license guard evidence.
4. Public/private separation evidence.
5. Validation commands and results.
6. Known limitations/deferred scope.

## Required Checks

At minimum:

```bash
git status --short
cd studio_suite/backend && python -m compileall app
cd studio_suite/frontend && npm run build -- --outDir /tmp/studio-suite-vite-build --emptyOutDir
```

Run targeted backend tests if an existing test framework and fixtures support this area. If not, state the test gap explicitly and keep changes small enough for PM review.

## Handoff Artifacts

Create:

- `studio_suite/docs/handoffs/2026-07-05-t003-legacy-caisse-minimal-flow.md`
- `studio_suite/docs/postmortems/2026-07-05-t003-legacy-caisse-minimal-flow.md`

Do not claim done unless checks actually ran or the blocker is explicit.
