# Instalacja Studio Suite

## Wymagania

- Python 3.10+
- PostgreSQL 14+
- Node.js 18+
- Docker + Docker Compose (opcjonalnie)

## Opcja A: Docker

```powershell
cd studio_suite
docker compose up -d --build
```

## Opcja B: lokalnie

### Backend

```powershell
cd studio_suite\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
# utworz plik .env z minimum:
# DATABASE_URL=postgresql://user:password@localhost:5432/studio_suite
# SECRET_KEY=change-me
uvicorn app.main:app --reload --port 8000
```

### Frontend

```powershell
cd studio_suite\frontend
npm install
npm run dev
```

## Pierwszy admin

```powershell
cd studio_suite
docker compose exec -T backend python scripts/create_admin.py admin password123
```
