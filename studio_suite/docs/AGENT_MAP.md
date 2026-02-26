# AGENT MAP (Studio Suite)

## Struktura
- `studio_suite/backend` - FastAPI + Celery + SQLAlchemy
- `studio_suite/frontend` - React + Vite + MUI
- `studio_suite/docker-compose.yml` - gĹ‚Ăłwny runtime
- `studio_suite/nginx` - pomocnicze konfiguracje nginx
- `studio_suite/scripts` - smoke/test narzÄ™dzia

## Krytyczne pliki
- Backend entry: `backend/app/main.py`
- Auth API: `backend/app/api/v1/auth.py`
- Frontend API client: `frontend/src/services/api.ts`
- Frontend websocket: `frontend/src/services/websocket.ts`
- Status page: `frontend/src/pages/StatusPage.tsx`
- Compose: `docker-compose.yml`
- Runtime env (nie commitowaÄ‡): `backend/.env`

## Routing produkcyjny (obecny)`r`n- Gateway reverse proxy: `gateway` (`192.168.200.115`)
- FE: `https://dev2.witold.ovh/`
- API: `https://dev2.witold.ovh/api/v1/...`

## Deploy flow`r`n0. Gateway: aktywny vhost `dev2.witold.ovh` w `gateway-services/nginx/conf.d`
1. Lokalnie: commit/push `master`
2. dev1:
   - `cd ~/projects/studio_suite_repo`
   - `git pull origin master`
   - `cd studio_suite`
   - `docker compose up -d --build`


