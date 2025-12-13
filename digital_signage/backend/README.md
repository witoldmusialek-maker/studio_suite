# Backend API

Backend systemu digital signage oparty na FastAPI.

## Struktura

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # Główny plik aplikacji
│   ├── config.py         # Konfiguracja
│   ├── database.py       # Połączenie z bazą danych
│   ├── models/           # Modele SQLAlchemy
│   ├── schemas/          # Schematy Pydantic
│   ├── api/              # Endpointy API
│   ├── services/         # Logika biznesowa
│   └── utils/            # Narzędzia pomocnicze
├── alembic/              # Migracje bazy danych
├── requirements.txt
└── .env.example
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

API dostępne pod: http://localhost:8000
Dokumentacja: http://localhost:8000/docs

