#!/bin/bash
# Skrypt instalacji backendu

echo "Instalacja backendu Digital Signage..."

# Tworzenie wirtualnego środowiska
cd backend
python3 -m venv venv
source venv/bin/activate

# Instalacja zależności
pip install --upgrade pip
pip install -r requirements.txt

# Tworzenie katalogów dla treści
mkdir -p content/original
mkdir -p content/processed
mkdir -p content/thumbnails

# Kopiowanie .env.example do .env (jeśli nie istnieje)
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Utworzono plik .env - uzupełnij konfigurację!"
fi

echo "Backend zainstalowany!"
echo "Następne kroki:"
echo "1. Skonfiguruj .env (DATABASE_URL, REDIS_URL, SECRET_KEY)"
echo "2. Utwórz bazę danych PostgreSQL"
echo "3. Uruchom migracje: alembic upgrade head"
echo "4. Uruchom serwer: uvicorn app.main:app --reload"

