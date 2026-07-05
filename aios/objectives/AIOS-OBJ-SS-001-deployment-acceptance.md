# AIOS-OBJ-SS-001 Deployment Acceptance — Studio Suite Development Environment

Date: 2026-07-05
Status: ACCEPTED
Project: Studio Suite
Objective: AIOS-OBJ-SS-001 — Controlled Development Deployment
Authority: Sponsor
Deployment target: 192.168.50.20
Environment: development
Branch: feature/legacy-caisse-flow
Deployed commit: e90af33aab554903e1e13aff1ba4c90588cd74bd

## Sponsor decision

Sponsor accepts the controlled deployment as completed.

Sponsor also authorizes the remaining HTTP smoke verification to be completed operationally by the PM without further Sponsor authorization.

Sponsor will review the running development environment.

## Acceptance boundary

This acceptance confirms completion of the one-time controlled development deployment authorized under AIOS-OBJ-SS-001.

This acceptance does not authorize:

- production deployment;
- deployment to new environments;
- merge or promotion to `master`;
- branch policy changes;
- infrastructure changes;
- network architecture changes;
- governance changes;
- deployment process redesign;
- long-term Deployment Authority assignment.

## Deployment evidence

Deployment completed on the current development target using the existing compose process:

```text
docker compose up -d --build
```

Post-deployment service state:

```text
backend           Up / healthy / 192.168.50.20:8003
backend_public    Up / healthy / 192.168.50.20:8004
db                Up / healthy
frontend          Up / 192.168.50.20:8082
frontend_public   Up / 192.168.50.20:8084
```

Database migration evidence:

```text
cashier_correction_audits table present
```

## Operational HTTP smoke completion

Timestamp:

```text
2026-07-05T17:00:04+00:00
```

Results:

```text
http://192.168.50.20:8003/health -> 200
http://192.168.50.20:8004/health -> 200
http://192.168.50.20:8082 -> 200
http://192.168.50.20:8084 -> 200
https://dev2.witold.ovh/health -> 200
```

HTTP smoke status: PASS.

## Rollback status

Rollback was not required.

## Remaining operational issues

No deployment-blocking operational issues remain for Sponsor review of the running development environment.

Still unresolved outside this deployment acceptance:

- long-term branch policy;
- merge/promote to `master`;
- production deployment;
- long-term Deployment Authority;
- future Objectives beyond accepted T-006 / next Controlled Pilot Track step.

## Consequence

AIOS-OBJ-SS-001 controlled deployment authorization is complete and expired after completion.

Studio Suite development environment is available for Sponsor review.
