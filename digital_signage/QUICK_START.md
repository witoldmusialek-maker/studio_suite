# Quick Start - Szybki Start Testowania

## Minimalne Wymagania do Testów

1. **PostgreSQL** - działająca baza danych
2. **Redis** - działający serwer Redis
3. **Python 3.10+** - dla backendu i klienta
4. **Node.js 18+** - dla frontendu

## Szybka Instalacja (Ubuntu/Debian)

```bash
# 1. Instalacja PostgreSQL i Redis
sudo apt update
sudo apt install -y postgresql redis-server python3-pip python3-venv nodejs npm

# 2. Utworzenie bazy danych
sudo -u postgres psql -c "CREATE DATABASE digital_signage;"
sudo -u postgres psql -c "CREATE USER signage_user WITH PASSWORD 'test123';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE digital_signage TO signage_user;"

# 3. Backend
cd digital_signage/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Konfiguracja .env
echo "DATABASE_URL=postgresql://signage_user:test123@localhost:5432/digital_signage" > .env
echo "REDIS_URL=redis://localhost:6379/0" >> .env
echo "SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')" >> .env

# Migracje
alembic revision --autogenerate -m "Initial"
alembic upgrade head

# Utworzenie admina
python scripts/create_admin.py admin password123

# 4. Frontend
cd ../frontend
npm install

# 5. Klient (opcjonalnie)
cd ../client
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Uruchomienie

### Terminal 1: Backend
```bash
cd digital_signage/backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### Terminal 2: Celery Worker
```bash
cd digital_signage/backend
source venv/bin/activate
celery -A app.celery_app worker --loglevel=info
```

### Terminal 3: Celery Beat
```bash
cd digital_signage/backend
source venv/bin/activate
celery -A app.celery_app beat --loglevel=info
```

### Terminal 4: Frontend
```bash
cd digital_signage/frontend
npm run dev
```

### Terminal 5: Klient (opcjonalnie)
```bash
cd digital_signage/client
source venv/bin/activate
python main.py
```

## Testowanie

1. Otwórz http://localhost:3000
2. Zaloguj się: admin / password123
3. Przejdź do "Wyświetlacze" - sprawdź czy klient się zarejestrował
4. Przejdź do "Treści" - wgraj testowy obraz
5. Przejdź do "Harmonogramy" - utwórz harmonogram
6. Sprawdź czy treść wyświetla się na kliencie

## API Docs

http://localhost:8000/docs - Swagger UI z wszystkimi endpointami

## Status

✅ Backend - Gotowy do testów
✅ Frontend - Podstawowe funkcje gotowe
✅ Klient - Podstawowa aplikacja gotowa

Wszystkie pliki są krótkie i modułowe - łatwo kontynuować rozwój!



