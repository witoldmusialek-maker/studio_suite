# AGENT MAP (Digital Signage)

## Struktura
- `digital_signage/backend` - FastAPI + Celery + SQLAlchemy
- `digital_signage/frontend` - React + Vite + MUI
- `digital_signage/docker-compose.yml` - główny runtime
- `digital_signage/nginx` - pomocnicze konfiguracje nginx
- `digital_signage/scripts` - smoke/test narzędzia

## Krytyczne pliki
- Backend entry: `backend/app/main.py`
- Auth API: `backend/app/api/v1/auth.py`
- Frontend API client: `frontend/src/services/api.ts`
- Frontend websocket: `frontend/src/services/websocket.ts`
- Status page: `frontend/src/pages/StatusPage.tsx`
- Compose: `docker-compose.yml`
- Runtime env (nie commitować): `backend/.env`

## Routing produkcyjny (obecny)`r`n- Gateway reverse proxy: `gateway` (`192.168.200.115`)
- FE: `https://dev2.witold.ovh/`
- API: `https://dev2.witold.ovh/api/v1/...`

## Deploy flow`r`n0. Gateway: aktywny vhost `dev2.witold.ovh` w `gateway-services/nginx/conf.d`
1. Lokalnie: commit/push `master`
2. dev1:
   - `cd ~/projects/projekt2_repo`
   - `git pull origin master`
   - `cd digital_signage`
   - `docker compose up -d --build`
