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

Po starcie uslugi sa dostepne pod:
- Frontend: `http://localhost:8082`
- Backend API: `http://localhost:8003/api/v1`
- Frontend public: `http://localhost:8084`
- Backend public API: `http://localhost:8004/api/v1`

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
# (opcjonalnie rozliczenia mailowe)
# SMTP_HOST=smtp.twoja-firma.pl
# SMTP_PORT=587
# SMTP_USERNAME=billing@twoja-firma.pl
# SMTP_PASSWORD=twoje-haslo
# SMTP_FROM_EMAIL=billing@twoja-firma.pl
# SMTP_FROM_NAME=Studio Suite Billing
# SMTP_USE_STARTTLS=true
# BILLING_REMINDER_DAYS_BEFORE_DUE=14,7,1
# BILLING_REMINDER_DAYS_AFTER_DUE=0,3,7,14
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
