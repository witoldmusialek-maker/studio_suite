# AGENT MAP (Digital Signage)

## Struktura
- `digital_signage/backend` - FastAPI + Celery + SQLAlchemy
- `digital_signage/frontend` - React + Vite + MUI
- `digital_signage/docker-compose.yml` - g³ówny runtime
- `digital_signage/nginx` - pomocnicze konfiguracje nginx
- `digital_signage/scripts` - smoke/test narzêdzia

## Krytyczne pliki
- Backend entry: `backend/app/main.py`
- Auth API: `backend/app/api/v1/auth.py`
- Frontend API client: `frontend/src/services/api.ts`
- Frontend websocket: `frontend/src/services/websocket.ts`
- Status page: `frontend/src/pages/StatusPage.tsx`
- Compose: `docker-compose.yml`
- Runtime env (nie commitowaæ): `backend/.env`

## Routing produkcyjny (obecny)
- FE: `https://dev.witold.ovh/`
- API: `https://dev.witold.ovh/api/v1/...`

## Deploy flow
1. Lokalnie: commit/push `master`
2. dev1:
   - `cd ~/projects/digital_signage_repo`
   - `git pull origin master`
   - `cd digital_signage`
   - `docker compose up -d --build`
