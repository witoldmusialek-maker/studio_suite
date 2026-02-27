# Analiza Studio Suite (aktualna)

## Status dokumentu
Ten plik zastapil poprzednia analize projektu Digital Signage.
Aktualny projekt dotyczy domeny salonowej i nie obejmuje wyswietlaczy ani dzwonkow.

## Zakres funkcjonalny
- Uwierzytelnianie i role (`admin`, `manager`, `employee`, `receptionist`)
- Zarzadzanie salonami i personelem
- Kartoteka klientow i kalendarz wizyt
- Cennik uslug i pakiety (forfety)
- Baza produktow/kolorow
- Raporty legacy

## Tryb danych
- Frontend korzysta z API (bez mockow) dla modulu klientow i kalendarza.
- Bootstrap danych operacyjnych:
  - `GET /api/v1/booking/bootstrap`
- Operacje zapisu:
  - `POST /api/v1/booking/clients`
  - `POST /api/v1/booking/appointments`
  - `POST /api/v1/booking/appointments/{appointment_id}/complete`

## Architektura
- Backend: FastAPI + SQLAlchemy + PostgreSQL
- Frontend: React + Vite + MUI
- Runtime docker compose: `db`, `backend`, `frontend`

## Moduly usuniete z projektu
- Wyswietlacze i monitoring wyswietlaczy
- System dzwonkow
- Klienty urzadzen (Python/Android)
- Celery i Redis w runtime

## Endpointy API (kluczowe)
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/resources/salons`
- `GET /api/v1/resources/staff`
- `GET /api/v1/resources/products?salon_id=...`
- `GET /api/v1/legacy/catalog?salon_id=...`
- `GET /api/v1/legacy/reports/summary`

## Operacyjnie
- Deploy: `studio_suite/scripts/deploy-dev2.ps1`
- Smoke: `studio_suite/scripts/smoke-test.ps1` (alias: `studio_suite/scripts/smoke_test.ps1`)
