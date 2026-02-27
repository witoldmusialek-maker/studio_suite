# AGENT MAP (Studio Suite)

## Aktualny zakres
Studio Suite to projekt domeny salonowej:
- auth i role
- salony, pracownicy, produkty
- cennik uslug i pakiety
- raporty legacy

Poza zakresem:
- wyswietlacze
- dzwonki
- klienci urzadzen
- Celery/Redis runtime

## Struktura
- `studio_suite/backend` - FastAPI + SQLAlchemy
- `studio_suite/frontend` - React + Vite + MUI
- `studio_suite/docker-compose.yml` - runtime (db, backend, frontend)
- `studio_suite/scripts` - deploy i smoke test

## Krytyczne pliki
- Backend entry: `backend/app/main.py`
- API routing: `backend/app/api/v1/__init__.py`
- Auth API: `backend/app/api/v1/auth.py`
- Resource API: `backend/app/api/v1/resources.py`
- Legacy APIs: `backend/app/api/v1/legacy_catalog.py`, `backend/app/api/v1/legacy_reports.py`
- Frontend API client: `frontend/src/services/api.ts`
- Frontend routing: `frontend/src/App.tsx`
- Compose: `docker-compose.yml`

## Deploy flow
1. commit/push `master`
2. `studio_suite/scripts/deploy-dev2.ps1`
3. ewentualne sprzatanie orphanow: `docker compose up -d --remove-orphans`
