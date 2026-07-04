# Studio Suite

Studio Suite to system do zarzadzania salonami: kalendarz wizyt, kartoteka klientow, cennik uslug, pakiety, magazyn, raporty i modul rezerwacji publicznej.

## Zakres projektu (stan na 20 marca 2026)

- Auth i role + 2FA (TOTP)
- Operacje salonowe (klienci, wizyty, zasoby, uslugi, produkty)
- Raporty i importy legacy
- Public booking (frontend + backend)
- Multi-tenant i rozliczenia
- Android SMS bridge (gateway)

## Struktura

```text
studio_suite/
  backend/   FastAPI API
  frontend/  React panel operacyjny
  android/   SMS bridge (Android)
  docs/      dokumentacja techniczna
  scripts/   deploy/smoke/setup
```

## Repozytorium GitHub

Projekt jest hostowany na GitHub: https://github.com/witoldmusialek-maker/studio_suite

Remote skonfigurowany dla deploy key na historycznym hoscie dev1 (2026-06-09); aktualny runtime operacyjny dziala na `192.168.50.20`:
```bash
git remote -v
# origin  git@github.com:witoldmusialek-maker/studio_suite.git (fetch)
# origin  git@github.com:witoldmusialek-maker/studio_suite.git (push)
```

Branche: `master`, `feature/legacy-caisse-flow`

Current operational branch: `feature/legacy-caisse-flow`.
`master` remains the remote default but is older than the current operational baseline.

## Szybki start

```powershell
cd studio_suite
docker compose up -d --build
docker compose exec -T backend python scripts/create_admin.py admin password123
```

Serwisy operacyjne:
- Frontend: http://192.168.50.20:8082
- Backend API: http://192.168.50.20:8003/api/v1
- Swagger: http://192.168.50.20:8003/docs
- Frontend public: http://192.168.50.20:8084
- Backend public: http://192.168.50.20:8004/api/v1

## Dokumentacja

- `studio_suite/QUICK_START.md`
- `studio_suite/TESTING.md`
- `studio_suite/docs/INSTALLATION.md`
- `studio_suite/docs/AGENT_START.md`
- `studio_suite/docs/RULES.md`
