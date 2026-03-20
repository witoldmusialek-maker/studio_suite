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

## Szybki start

```powershell
cd studio_suite
docker compose up -d --build
docker compose exec -T backend python scripts/create_admin.py admin password123
```

Serwisy lokalne:
- Frontend: http://localhost:8082
- Backend API: http://localhost:8003/api/v1
- Swagger: http://localhost:8003/docs
- Frontend public: http://localhost:8084
- Backend public: http://localhost:8004/api/v1

## Dokumentacja

- `studio_suite/QUICK_START.md`
- `studio_suite/TESTING.md`
- `studio_suite/docs/INSTALLATION.md`
- `studio_suite/docs/AGENT_START.md`
