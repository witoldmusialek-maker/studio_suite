
CONTINUE
Current State
Source repo: witoldmusialek-maker/studio_suite (private)
Dev server: 192.168.200.116
Deploy path: ~/projects/studio_suite_repo/studio_suite
URL: https://dev2.witold.ovh/
API: /api/v1 (frontend uses relative API_URL)
Standard Deploy
cd ~/projects/studio_suite_repo
git pull origin master
cd studio_suite
docker compose up -d --build
docker compose ps

Quick Diagnostics
docker compose logs backend --tail 80
docker compose logs frontend --tail 80

Notes
Websocket (socket.io) is LAN-only.
On dev2.witold.ovh warnings are expected if backend has no socket endpoint.
Operacyjny workflow (stan aktualny)
Branching
master = stabilne wydania
develop = integracja zmian
feature/* = praca nad pojedynczym zadaniem
Deploy dev1 (jednym poleceniem)
Skrypt:

studio_suite/scripts/deploy-dev1.ps1
Uruchomienie:
Set-Location C:\Users\Wit\projekty\cline\projekt2\studio_suite
.\scripts\deploy-dev1.ps1 -DevHost dev1 -Branch master

Co robi:

SSH na dev1
git fetch + checkout branch + git pull
docker compose up -d --build
docker compose ps
Lokalny smoke test publicznego URL
Smoke test
Skrypt:

studio_suite/scripts/smoke-test.ps1
Uruchomienie:
.\scripts\smoke-test.ps1

Sprawdza:

/ => 200
/health => 200
/api/v1/auth/login (GET) => 405
Synchronizacja danych lokalny -> dev
Skrypt:

studio_suite/scripts/sync-to-dev.ps1
Uruchomienie:
.\scripts\sync-to-dev.ps1 -DevHost dev1

Zakres:

dump/restore PostgreSQL
sync backend/content
Synchronizacja danych dev -> lokalny
Skrypt:

studio_suite/scripts/sync-from-dev.ps1
Uruchomienie:
.\scripts\sync-from-dev.ps1 -DevHost dev1

Zakres:

dump/restore PostgreSQL
sync backend/content
SSH
Alias w C:\Users\Wit\.ssh\config:

dev1 -> 192.168.200.116

Gateway routing
- Host: gateway (192.168.200.115)
- Nginx config dir: /home/witold/gateway-services/nginx/conf.d
- Script: studio_suite/scripts/setup-gateway-dev2-nginx.ps1


