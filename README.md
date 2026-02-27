# Studio Suite

Studio Suite to system do zarzadzania salonami: kalendarz wizyt, kartoteka klientow, cennik uslug, pakiety (forfety), baza produktow i raporty legacy.

## Zakres projektu

Projekt **nie** zawiera juz modulow Digital Signage:
- brak wyswietlaczy
- brak dzwonkow
- brak klientow urzadzen

## Struktura

```text
studio_suite/
  backend/   FastAPI API (auth, resources, legacy catalog, legacy reports)
  frontend/  React panel webowy
  docs/      dokumentacja
  scripts/   skrypty pomocnicze
```

## Szybki start

```powershell
cd studio_suite
docker compose up -d --build
```

Serwisy:
- Frontend: http://localhost:8082
- Backend API: http://localhost:8003/api/v1
- Swagger: http://localhost:8003/docs

## Dokumentacja

- `studio_suite/QUICK_START.md`
- `studio_suite/docs/INSTALLATION.md`
- `ANALIZA_STUDIO_SUITE.md`
