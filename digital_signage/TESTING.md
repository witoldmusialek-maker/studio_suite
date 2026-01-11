# Instrukcje Testowania Systemu

## Status - Gotowe do Testowania

System jest gotowy do podstawowych testów:
- ✅ Backend: Wszystkie 9 etapów zakończone
- ✅ Frontend: Podstawowe funkcje (logowanie, wyświetlacze, status, treści)
- ✅ Klient: Podstawowa aplikacja wyświetlacza

## Przygotowanie do Testów

### 1. Backend

```bash
cd digital_signage/backend

# Utworzenie środowiska wirtualnego
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalacja zależności
pip install -r requirements.txt

# Konfiguracja .env
cp env_example.txt .env
# Edytuj .env i uzupełnij:
# - DATABASE_URL (np. postgresql://user:pass@localhost:5432/digital_signage)
# - REDIS_URL (np. redis://localhost:6379/0)
# - SECRET_KEY (wygeneruj losowy klucz)

# Utworzenie bazy danych PostgreSQL
createdb digital_signage  # lub przez psql

# Migracje
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# Utworzenie użytkownika admin
python scripts/create_admin.py admin password123

# Uruchomienie serwera
uvicorn app.main:app --reload
```

### 2. Celery (w osobnym terminalu)

```bash
cd digital_signage/backend
source venv/bin/activate

# Worker
celery -A app.celery_app worker --loglevel=info

# Beat (w osobnym terminalu)
celery -A app.celery_app beat --loglevel=info
```

### 3. Frontend

```bash
cd digital_signage/frontend

# Instalacja
npm install

# Uruchomienie
npm run dev
```

### 4. Klient (opcjonalnie - do testowania wyświetlacza)

```bash
cd digital_signage/client

# Instalacja
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Konfiguracja
# Edytuj config.py - ustaw SERVER_URL

# Uruchomienie
python main.py
```

## Scenariusze Testowe

### Test 1: Autentykacja

1. Otwórz http://localhost:3000
2. Zaloguj się jako admin (admin/password123)
3. Sprawdź czy dashboard się wyświetla

### Test 2: Rejestracja Wyświetlacza

1. Uruchom klienta (`python client/main.py`)
2. Sprawdź w panelu czy wyświetlacz się zarejestrował
3. Sprawdź czy status jest "online"

### Test 3: Upload Treści

1. W panelu przejdź do "Treści"
2. Kliknij "Upload"
3. Wybierz plik (obraz, PDF, Excel, video)
4. Sprawdź czy plik się wgrał
5. Sprawdź czy miniatura się wygenerowała (dla obrazów/PDF)

### Test 4: Harmonogram

1. Przejdź do "Harmonogramy"
2. Utwórz nowy harmonogram:
   - Wybierz treść
   - Wybierz wyświetlacz
   - Ustaw czas (np. teraz + 1 minuta do teraz + 5 minut)
3. Sprawdź czy harmonogram się zapisał

### Test 5: Wyświetlanie na Kliencie

1. Uruchom klienta
2. Sprawdź czy klient pobiera harmonogram
3. Sprawdź czy treść się wyświetla zgodnie z harmonogramem

### Test 6: Monitoring

1. Zatrzymaj klienta (Ctrl+C)
2. Poczekaj 2 minuty
3. Sprawdź w panelu "Status" czy wyświetlacz jest offline
4. Sprawdź w "Alerty" czy pojawił się alert

### Test 7: Raporty

1. Przejdź do "Raporty"
2. Wygeneruj raport dzienny
3. Sprawdź czy dane się wyświetlają
4. Eksportuj do CSV

## Endpointy API do Testowania

### Swagger UI
http://localhost:8000/docs

### Przykładowe testy przez curl

```bash
# Logowanie
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password123"}'

# Lista wyświetlaczy (wymaga tokena)
curl -X GET http://localhost:8000/api/v1/displays \
  -H "Authorization: Bearer <token>"

# Upload treści (wymaga tokena)
curl -X POST http://localhost:8000/api/v1/content/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@test_image.jpg"
```

## Problemy i Rozwiązania

### Problem: Błąd połączenia z bazą danych
**Rozwiązanie:** Sprawdź czy PostgreSQL działa i czy DATABASE_URL jest poprawny

### Problem: Błąd połączenia z Redis
**Rozwiązanie:** Sprawdź czy Redis działa i czy REDIS_URL jest poprawny

### Problem: Klient nie może się zarejestrować
**Rozwiązanie:** Sprawdź czy SERVER_URL w config.py jest poprawny

### Problem: Treści się nie wyświetlają
**Rozwiązanie:** Sprawdź czy harmonogram jest aktywny i czy czas jest poprawny

## Następne Kroki

Po podstawowych testach można kontynuować z:
- Dokończenie frontendu (harmonogramy, raporty, dzwonki)
- Rozszerzenie klienta (obsługa wszystkich formatów, cache)
- Integracja Google Drive
- Graficzny edytor układu



