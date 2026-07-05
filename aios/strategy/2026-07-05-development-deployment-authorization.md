# Studio Suite Decision — Development Deployment Authorization

Date: 2026-07-05
Status: AUTHORIZED
Project: Studio Suite
Authority: Sponsor
Active Objective: AIOS-OBJ-SS-001
Authorization type: single controlled development deployment
Expires: after completion of this deployment

## Sponsor decision

Sponsor authorizes the Program Manager to perform a single controlled deployment of the approved implementation to the Studio Suite development environment.

## Purpose

Validate the completed operational work in the running system and allow Sponsor review.

## Scope

This authorization applies only to:

- changes already accepted within approved Objectives;
- the current development environment;
- the existing deployment process;
- the current deployment target.

## PM authorization

PM is authorized to:

- prepare the deployment;
- execute the deployment;
- verify service health;
- verify application availability;
- verify database migrations, if any;
- restore service if rollback is required;
- report deployment results.

## Restrictions

This authorization does not include:

- production deployment;
- deployment to new environments;
- merge or promotion to `master`;
- branch policy changes;
- infrastructure changes;
- network architecture changes;
- governance changes;
- deployment process redesign.

## Expected deliverable

PM returns a Deployment Report containing:

- deployed commit(s);
- deployment target;
- deployment timestamp;
- health verification;
- smoke test results;
- rollback status, if applicable;
- remaining operational issues;
- recommendation for next work.

## Current target and process

Current deployment target from Project Memory / existing deploy scripts:

```text
192.168.50.20
```

Current branch / integration line:

```text
feature/legacy-caisse-flow
```

Existing deployment process:

```text
git fetch/checkout/pull on target
cd studio_suite
docker compose up -d --build
docker compose ps
health-only smoke checks
```

## Boundary note

This decision is a one-time development deployment authorization. It does not settle long-term Deployment Authority or branch policy.
