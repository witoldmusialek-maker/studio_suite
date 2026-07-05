# Legacy CAISSE transition module

Legacy CAISSE is a transitional salon cashier workflow. It uses the modern tenant, salon, staff, service, bundle, product, sale and payment data model.

Out of scope: Bureau reconstruction, WDD/FIC/NDX runtime checks, CAISSE to Bureau transfer, exploitation reports and file database synchronization.

Core scope:
- cashier fiche entry with legacy staff and service codes,
- bundles/forfaits, discounts and payment capture,
- current-month fiche list,
- salon expenses, cash session and staff presence,
- tenant module license LEGACY_CAISSE and salon access checks.
