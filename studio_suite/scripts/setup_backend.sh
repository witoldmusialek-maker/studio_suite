#!/bin/bash
# Skrypt instalacji backendu

echo "Instalacja backendu Studio Suite..."

# Tworzenie wirtualnego Ĺ›rodowiska
cd backend
python3 -m venv venv
source venv/bin/activate

# Instalacja zaleĹĽnoĹ›ci
pip install --upgrade pip
pip install -r requirements.txt

# Tworzenie katalogĂłw dla treĹ›ci
mkdir -p content/original
mkdir -p content/processed
mkdir -p content/thumbnails

# Kopiowanie .env.example do .env (jeĹ›li nie istnieje)
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Utworzono plik .env - uzupeĹ‚nij konfiguracjÄ™!"
fi

echo "Backend zainstalowany!"
echo "NastÄ™pne kroki:"
echo "1. Skonfiguruj .env (DATABASE_URL, REDIS_URL, SECRET_KEY)"
echo "2. UtwĂłrz bazÄ™ danych PostgreSQL"
echo "3. Uruchom migracje: alembic upgrade head"
echo "4. Uruchom serwer: uvicorn app.main:app --reload"


