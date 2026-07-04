# AGENT MAP (Studio Suite)

## Aktualny zakres
Studio Suite to projekt domeny salonowej:
- auth i role
- salony, pracownicy, produkty
- kartoteka klientow i kalendarz wizyt
- cennik uslug i pakiety
- raporty legacy
- public booking
- multi-tenant i rozliczenia
- sms gateway (android)

Poza zakresem:
- wyswietlacze
- dzwonki
- Celery/Redis runtime

## Struktura
- `studio_suite/backend` - FastAPI + SQLAlchemy
- `studio_suite/frontend` - React + Vite + MUI (panel operacyjny)
- `studio_suite/android/sms_bridge` - bramka SMS na Android
- `studio_suite/docker-compose.yml` - runtime (db, backend, frontend, backend_public, frontend_public)
- `studio_suite/scripts` - deploy i smoke test

## Dane operacyjne
- Frontend korzysta z API (bez mockow) dla klientow, wizyt i rozliczen.
- Endpoint bootstrap: `GET /api/v1/booking/bootstrap`
- Endpointy zapisu:
  - `POST /api/v1/booking/clients`
  - `POST /api/v1/booking/appointments`
  - `POST /api/v1/booking/appointments/{appointment_id}/complete`

## Krytyczne pliki
- Backend entry: `backend/app/main.py`
- Backend public entry: `backend/app/public_main.py`
- API routing: `backend/app/api/v1/__init__.py`
- Auth API: `backend/app/api/v1/auth.py`
- Resource API: `backend/app/api/v1/resources.py`
- Legacy APIs: `backend/app/api/v1/legacy_catalog.py`, `backend/app/api/v1/legacy_reports.py`
- Public APIs: `backend/app/api/v1/public_auth.py`, `backend/app/api/v1/public_booking.py`
- Frontend API client: `frontend/src/services/api.ts`
- Frontend routing: `frontend/src/App.tsx`
- Compose: `docker-compose.yml`

## Deploy flow
1. commit/push `feature/legacy-caisse-flow` (current operational branch)
2. `studio_suite/scripts/deploy-dev2.ps1`
3. ewentualne sprzatanie orphanow: `docker compose up -d --remove-orphans`
4. health smoke: `studio_suite/scripts/smoke-test.ps1 -HealthOnly` (alias kompatybilnosci: `smoke_test.ps1`)
5. authenticated smoke requires approved credentials/TOTP handling; do not commit secrets.

## Hygiena worktree
- cache Android: `android/sms_bridge/.gradle/`, `android/sms_bridge/app/build/` sa lokalne i ignorowane
- lokalne artefakty root (`2.7z`, `CENY kalkulacja pakietow kwiecien 2025.xls`) sa ignorowane
