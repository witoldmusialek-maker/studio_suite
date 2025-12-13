# Instalacja Systemu Digital Signage

## Wymagania Systemowe

### Serwer (Ubuntu VM na Hyper-V)
- Ubuntu 22.04 LTS
- 4 vCPU (minimum 2)
- 8 GB RAM (minimum 4 GB)
- 100 GB dysk (SSD preferowane)

### Oprogramowanie
- Python 3.10+
- PostgreSQL 14+
- Redis 7+
- Node.js 18+
- FFmpeg
- Nginx (opcjonalnie)

## Instalacja na Ubuntu VM

### 1. Aktualizacja systemu
```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Instalacja podstawowych narzędzi
```bash
sudo apt install -y git curl wget build-essential
```

### 3. Instalacja PostgreSQL
```bash
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Utworzenie bazy danych
sudo -u postgres psql
CREATE DATABASE digital_signage;
CREATE USER signage_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE digital_signage TO signage_user;
\q
```

### 4. Instalacja Redis
```bash
sudo apt install -y redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### 5. Instalacja Python i pip
```bash
sudo apt install -y python3.10 python3-pip python3-venv
```

### 6. Instalacja FFmpeg
```bash
sudo apt install -y ffmpeg
```

### 7. Instalacja Node.js
```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### 8. Konfiguracja Firewall
```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

## Instalacja Aplikacji

### Backend
```bash
cd digital_signage/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edytuj .env i uzupełnij konfigurację
```

### Frontend
```bash
cd digital_signage/frontend
npm install
cp .env.example .env
# Edytuj .env i uzupełnij konfigurację
```

### Klient
```bash
cd digital_signage/client
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Konfiguracja

Zobacz szczegóły w plikach `.env.example` w każdym katalogu.

## Uruchomienie

### Backend
```bash
cd backend
source venv/bin/activate
alembic upgrade head  # Migracje bazy danych
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm start
```

### Klient (na wyświetlaczu)
```bash
cd client
source venv/bin/activate
python main.py
```

## Następne Kroki

1. Utworzenie pierwszego użytkownika admin
2. Konfiguracja wyświetlaczy
3. Upload pierwszej treści
4. Konfiguracja harmonogramów

