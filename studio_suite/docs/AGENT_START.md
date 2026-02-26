# AGENT START (Studio Suite)

## Cel
Szybki start bez peĹ‚nego skanowania repo.

## Czytaj w tej kolejnoĹ›ci (max 2-3 min)
1. `studio_suite/docs/AGENT_MAP.md`
2. `studio_suite/CONTINUE.md`
3. `studio_suite/docker-compose.yml`
4. `studio_suite/frontend/src/services/api.ts`
5. `studio_suite/backend/app/main.py`
6. `studio_suite/backend/app/api/v1/auth.py`

## Szybka diagnostyka (lokalnie)
- `docker compose -f studio_suite/docker-compose.yml ps`
- `docker compose -f studio_suite/docker-compose.yml logs backend --tail 80`
- `docker compose -f studio_suite/docker-compose.yml logs frontend --tail 80`

## Szybka diagnostyka (dev1 app host)
- `ssh witold@192.168.200.116`
- `cd ~/projects/studio_suite_repo/studio_suite`
- `docker compose ps`
- `docker compose logs backend --tail 80`
- `docker compose logs frontend --tail 80`

## NajczÄ™stsze puĹ‚apki
- mixed content (`http://` przy `https://`) -> sprawdĹş `frontend/src/services/api.ts` i `VITE_API_URL`
- CORS preflight 400 -> sprawdĹş `backend/.env` `CORS_ORIGINS`
- websocket error na dev2.witold.ovh -> akceptowalne (LAN-only funkcja)

## Definition of done (deploy)
1. `git push` na `master`
2. `dev1`: `git pull && docker compose up -d --build`
3. gateway ma aktywny vhost `dev2.witold.ovh` (`setup-gateway-dev2-nginx.ps1`)`r`n4. `https://dev2.witold.ovh/` dziaĹ‚a i brak czerwonych bĹ‚Ä™dĂłw API w Network


