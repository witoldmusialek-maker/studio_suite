# AGENT START (Digital Signage)

## Cel
Szybki start bez pełnego skanowania repo.

## Czytaj w tej kolejności (max 2-3 min)
1. `digital_signage/docs/AGENT_MAP.md`
2. `digital_signage/CONTINUE.md`
3. `digital_signage/docker-compose.yml`
4. `digital_signage/frontend/src/services/api.ts`
5. `digital_signage/backend/app/main.py`
6. `digital_signage/backend/app/api/v1/auth.py`

## Szybka diagnostyka (lokalnie)
- `docker compose -f digital_signage/docker-compose.yml ps`
- `docker compose -f digital_signage/docker-compose.yml logs backend --tail 80`
- `docker compose -f digital_signage/docker-compose.yml logs frontend --tail 80`

## Szybka diagnostyka (dev1 app host)
- `ssh witold@192.168.200.116`
- `cd ~/projects/projekt2_repo/digital_signage`
- `docker compose ps`
- `docker compose logs backend --tail 80`
- `docker compose logs frontend --tail 80`

## Najczęstsze pułapki
- mixed content (`http://` przy `https://`) -> sprawdź `frontend/src/services/api.ts` i `VITE_API_URL`
- CORS preflight 400 -> sprawdź `backend/.env` `CORS_ORIGINS`
- websocket error na dev2.witold.ovh -> akceptowalne (LAN-only funkcja)

## Definition of done (deploy)
1. `git push` na `master`
2. `dev1`: `git pull && docker compose up -d --build`
3. gateway ma aktywny vhost `dev2.witold.ovh` (`setup-gateway-dev2-nginx.ps1`)`r`n4. `https://dev2.witold.ovh/` działa i brak czerwonych błędów API w Network
