# Backend API (Studio Suite)

Backend oparty na FastAPI, skupiony na domenie salonowej.

## Moduly API
- `/api/v1/auth` - logowanie i zarzadzanie uzytkownikami
- `/api/v1/resources` - salony, pracownicy, produkty
- `/api/v1/legacy/catalog` - cennik uslug i pakiety
- `/api/v1/legacy/reports` - raporty legacy

## Struktura
```text
backend/
  app/
    api/
    models/
    schemas/
    services/
    utils/
  alembic/
  requirements.txt
```

## Uruchomienie lokalne
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API: `http://localhost:8000`
Swagger: `http://localhost:8000/docs`

## Import danych legacy
```bash
python scripts/import_legacy_seed.py --input-dir C:\tmp\legacy_05 --truncate --salon-code 05 --salon-name PULAWSKA
```
