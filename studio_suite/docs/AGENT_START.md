# AGENT START (Studio Suite)

## Cel
Szybki start pracy nad aktualnym projektem salonowym (bez modulow Digital Signage) z runtime direct + public.

## Czytaj w tej kolejnosci (2-3 min)
1. `studio_suite/docs/AGENT_MAP.md`
2. `studio_suite/docs/AGENT_REMOTE_SETUP.md`
3. `README.md`
4. `studio_suite/docker-compose.yml`
5. `studio_suite/frontend/src/services/api.ts`
6. `studio_suite/backend/app/main.py`
7. `studio_suite/backend/app/public_main.py`
8. `studio_suite/backend/app/api/v1/auth.py`
9. `studio_suite/backend/app/api/v1/public_booking.py`

## Szybka diagnostyka lokalnie
- `docker compose -f studio_suite/docker-compose.yml ps`
- `docker compose -f studio_suite/docker-compose.yml logs backend --tail 80`
- `docker compose -f studio_suite/docker-compose.yml logs frontend --tail 80`
- `docker compose -f studio_suite/docker-compose.yml logs backend_public --tail 80`
- `docker compose -f studio_suite/docker-compose.yml logs frontend_public --tail 80`

## Worktree hygiene (lokalnie)
- Android build cache: `studio_suite/android/sms_bridge/.gradle`, `studio_suite/android/sms_bridge/app/build`
- Szybkie czyszczenie:
  - `rm -rf studio_suite/android/sms_bridge/.gradle studio_suite/android/sms_bridge/app/build`

## Szybka diagnostyka hosta operacyjnego
- `ssh studio-suite-dev` albo `ssh 192.168.50.20`
- `cd ~/projects/projekt2_repo/studio_suite`
- `docker compose ps`
- `docker compose logs backend --tail 80`
- `docker compose logs frontend --tail 80`
- `docker compose logs backend_public --tail 80`
- `docker compose logs frontend_public --tail 80`

## Definition of done (deploy)
1. `git push origin feature/legacy-caisse-flow`
2. `powershell -ExecutionPolicy Bypass -File .\studio_suite\scripts\deploy-dev2.ps1`
3. health smoke direct i public przechodza (`-HealthOnly`)
4. authenticated smoke wymaga jawnie zatwierdzonych credentials/TOTP flow; nie commituj sekretow.
