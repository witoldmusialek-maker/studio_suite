# SMS Bridge (Android)

Aplikacja wystawia lokalny endpoint HTTP i wysyla SMS przez telefon.

## Parowanie przez panel
1. W panelu: Pomoc -> Parowanie telefonu SMS -> wygeneruj kod.
2. W aplikacji wpisz adres panelu i kod parowania.
3. Kliknij `Sparuj przez panel`.
4. Aplikacja pobierze token i uruchomi gateway.

## Endpointy telefonu
- `GET /health` -> `{ "status": "ok" }`
- `POST /send` JSON: `{ "to": "+48123123123", "message": "tekst" }`
- `GET /send?to=...&message=...`

Po sparowaniu autoryzacja jest wymagana (`Authorization: Bearer <token>`).
