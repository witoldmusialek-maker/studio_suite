# Backend API

Backend systemu Studio Suite oparty na FastAPI.

## Struktura

```
backend/
â”śâ”€â”€ app/
â”‚   â”śâ”€â”€ __init__.py
â”‚   â”śâ”€â”€ main.py           # GĹ‚Ăłwny plik aplikacji
â”‚   â”śâ”€â”€ config.py         # Konfiguracja
â”‚   â”śâ”€â”€ database.py       # PoĹ‚Ä…czenie z bazÄ… danych
â”‚   â”śâ”€â”€ models/           # Modele SQLAlchemy
â”‚   â”śâ”€â”€ schemas/          # Schematy Pydantic
â”‚   â”śâ”€â”€ api/              # Endpointy API
â”‚   â”śâ”€â”€ services/         # Logika biznesowa
â”‚   â””â”€â”€ utils/            # NarzÄ™dzia pomocnicze
â”śâ”€â”€ alembic/              # Migracje bazy danych
â”śâ”€â”€ requirements.txt
â””â”€â”€ .env.example
```

## Instalacja

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Uruchomienie

```bash
uvicorn app.main:app --reload
```

API dostÄ™pne pod: http://localhost:8000
Dokumentacja: http://localhost:8000/docs


## Import danych legacy (FIC)

Po pierwszym uruchomieniu mozesz zaimportowac baze starego systemu do tabel aplikacji:

```bash
cd backend
python scripts/import_legacy_seed.py --input-dir C:\tmp\legacy_05 --truncate --salon-code 05 --salon-name PULAWSKA
```

Po imporcie dostepne sa endpointy:

- `GET /api/v1/legacy/reports/summary`
- `GET /api/v1/legacy/reports/forfaits?from_date=2024-09-01&to_date=2024-09-30`
- `GET /api/v1/legacy/reports/services-by-worker?from_date=2024-09-01&to_date=2024-09-30`
- `GET /api/v1/legacy/reports/daily-summary?from_date=2026-02-01&to_date=2026-02-28`
- `GET /api/v1/legacy/reports/forfait-transactions?from_date=2026-02-01&to_date=2026-02-28`
- `GET /api/v1/legacy/reports/services-aggregate?from_date=2026-02-01&to_date=2026-02-28`
- `GET /api/v1/legacy/reports/cashflow?from_date=2026-02-01&to_date=2026-02-28`
- `GET /api/v1/legacy/reports/stat7-worker`
- `GET /api/v1/legacy/reports/edservice-aggregate`

