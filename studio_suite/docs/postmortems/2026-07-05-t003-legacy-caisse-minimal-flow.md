# Postmortem — T-003 Legacy CAISSE Minimal Flow

Date: 2026-07-05
Status: ready-for-review
Objective: AIOS-OBJ-SS-003 — Legacy CAISSE Minimal Flow

## What happened

The existing Legacy CAISSE implementation already contained most of the minimal create/list cashier path. The implementation work focused on turning that path into a reviewable first delivery slice by adding focused tests and closing boundary gaps before persistence.

## TDD notes

RED evidence:

- Initial local pytest could not collect because the active Hermes Python environment lacked project dependencies (`sqlalchemy`).
- A project-local backend `.venv` was created and dependencies installed from `requirements.txt` plus `pytest`.
- After test harness adjustment for SQLite metadata/index limitations, tests produced the expected RED result:

```text
1 passed, 2 failed
- staff from another salon was not rejected
- inactive service was not rejected
```

GREEN evidence:

```text
3 passed, 7 warnings
```

## Issues found

1. `create_fiche` validated user access to the target salon, but did not validate that the staff member on a sale line belonged to that salon.
2. `create_fiche` accepted inactive/missing service identifiers for service lines.
3. Test setup against full SQLAlchemy metadata hit duplicate-index limitations under SQLite, so the test fixture creates only the tables needed for this slice and temporarily suppresses index creation for those tables.

## Fix applied

Added pre-persistence line validation in `legacy_caisse.py`:

- staff must belong to the target salon or have an active `StaffSalonMembership` for it;
- service lines require an active `ServiceCatalogItem`;
- product lines require an active `SalonProductCatalogItem` link;
- bundle lines require an active `BundleCatalog`;
- validation happens before `Sale` is flushed, so rejected payloads do not leave partial sale rows in the session.

## What stayed out of scope

- frontend redesign;
- public booking changes;
- deployment scripts/nginx changes;
- WinDev/Bureau reconstruction;
- production deployment;
- merge to `master`.

## Follow-up recommendations

1. In a later ticket, add API-level tests using FastAPI dependency overrides once a stable project test harness exists.
2. In a later ticket, decide whether salon-service availability should require an explicit `SalonServiceCatalogItem` link or whether active global services remain valid for all salons.
3. Keep authenticated browser smoke as a separate controlled step because credentials/TOTP are intentionally not committed.
