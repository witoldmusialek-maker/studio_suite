# AGENT REMOTE SETUP (Windows 10 + VS Code + Codex over SSH)

## Cel
Szybkie uruchomienie pracy na nowym komputerze Windows 10, gdzie kod edytujesz zdalnie na dev przez SSH (VS Code Remote SSH + Codex).

## Aktualny stan projektu
- Projekt: `studio_suite` (domena salonowa)
- Brak modulow Digital Signage (wyswietlacze, dzwonki, klienci urzadzen)
- Runtime: `db`, `backend`, `frontend` (docker compose)
- Glowna galaz: `master`

## Wymagania na nowym komputerze (Windows 10)
- VS Code
- OpenSSH client (`ssh` w terminalu)
- Git
- Dostep SSH do hosta dev (`dev1`)
- Dostep do repo (push/pull)

## Rozszerzenia VS Code
- `Remote - SSH` (Microsoft)
- `Python` (Microsoft)
- `Docker` (Microsoft) - opcjonalnie

## Konfiguracja SSH (lokalnie)
Plik: `%USERPROFILE%\\.ssh\\config`

```sshconfig
Host dev1
    HostName 192.168.200.116
    User witold
    IdentityFile ~/.ssh/id_rsa
    ServerAliveInterval 30
    ServerAliveCountMax 120
```

Po konfiguracji sprawdz:

```powershell
ssh dev1 "hostname && whoami"
```

## Otwieranie workspace przez SSH
1. VS Code -> `Remote-SSH: Connect to Host...` -> `dev1`
2. `File -> Open Folder...`
3. Otworz folder:
   - `~/projects/projekt2_repo`
4. Pracuj w tym repo (to jest zrodlo deployowane przez skrypt).

## Najwazniejsze sciezki
- Repo root: `~/projects/projekt2_repo`
- Aplikacja: `~/projects/projekt2_repo/studio_suite`
- Backend: `~/projects/projekt2_repo/studio_suite/backend`
- Frontend: `~/projects/projekt2_repo/studio_suite/frontend`

## Podstawowe komendy operacyjne (na dev1)
```bash
cd ~/projects/projekt2_repo/studio_suite
docker compose ps
docker compose logs backend --tail 120
docker compose logs frontend --tail 120
```

## Uruchamianie / odswiezanie stacka
```bash
cd ~/projects/projekt2_repo/studio_suite
docker compose up -d --build --remove-orphans
```

## Smoke test
```powershell
powershell -ExecutionPolicy Bypass -File .\studio_suite\scripts\smoke-test.ps1 -BaseUrl http://192.168.200.116:8003
```

Opcjonalnie publiczny:

```powershell
powershell -ExecutionPolicy Bypass -File .\studio_suite\scripts\smoke-test.ps1 -BaseUrl https://dev2.witold.ovh
```

Alias kompatybilnosci: `studio_suite/scripts/smoke_test.ps1` (deleguje do `smoke-test.ps1`).

## Standardowy flow pracy
1. `git checkout master`
2. `git pull origin master`
3. Zmiany kodu
4. Szybka walidacja:
   - frontend: `cd studio_suite/frontend && npm run build`
   - backend: `cd studio_suite/backend && python -m compileall app`
5. `git add -A && git commit -m "..."`
6. `git push origin master`
7. Deploy:
   - `powershell -ExecutionPolicy Bypass -File .\studio_suite\scripts\deploy-dev2.ps1`

## Co robic gdy backend jest unhealthy
1. Logi:
```bash
cd ~/projects/projekt2_repo/studio_suite
docker compose logs --no-color backend --tail 200
```
2. Czeste przyczyny:
- brak/blad env (`backend/.env`)
- niekompatybilne dane po zmianie modeli
- brakujace migracje

## Srodowisko i sekrety
- Konfiguracja backendu: `studio_suite/backend/.env`
- `SECRET_KEY` musi byc ustawiony
- Aktualny kod ignoruje nieuzywane legacy zmienne env (`extra=ignore`)

## Krytyczne pliki do orientacji
- `studio_suite/docs/AGENT_MAP.md`
- `studio_suite/docs/AGENT_START.md`
- `studio_suite/backend/app/main.py`
- `studio_suite/backend/app/api/v1/__init__.py`
- `studio_suite/frontend/src/App.tsx`
- `studio_suite/docker-compose.yml`
- `studio_suite/scripts/deploy-dev2.ps1`

## Uwagi praktyczne
- Jesli po zmianie compose widzisz stare kontenery, uruchom:
```bash
docker compose up -d --remove-orphans
```
- Nie pracuj w kopii repo poza `~/projects/projekt2_repo`, bo deploy skrypt bazuje na tej lokalizacji.
