# Studio Suite

Panel i API dla domeny salonowej + public booking + SMS gateway.

## Moduly aktywne

- `auth` + role + TOTP (`/api/v1/auth`)
- `booking` (kalendarz, klienci, wizyty)
- `resources` (salony, pracownicy, produkty)
- `legacy/catalog` (uslugi, pakiety)
- `legacy/reports` + importy
- `inventory` + receptury + stany
- `payments`
- `tenants` + licencje
- `public booking` (`/api/v1/public/*`, `frontend_public`)
- `android sms bridge` (`android/sms_bridge`)

## Runtime (docker compose)

- `db`
- `backend` (panel operacyjny, port `8003`)
- `frontend` (panel operacyjny, port `8082`)
- `backend_public` (public API, port `8004`)
- `frontend_public` (public booking, port `8084`)

## Struktura

```text
studio_suite/
  backend/
  frontend/
  android/
  docs/
  scripts/
```
