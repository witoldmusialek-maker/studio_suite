# Analiza Systemu Digital Signage - Szczegółowa Specyfikacja

## 1. Wymagania Funkcjonalne - Aktualizacja

### MIN-imum
1. ✅ Wyświetlanie: Excel, PDF (skalowanie na jedną stronę), MPG, JPG
2. ✅ Obrót 90° (3 monitory pionowe obok siebie)
3. ✅ Równoległe/osobne wyświetlanie na 4 TV (2× 1 piętro, 1× parter, 1× 2 piętro) przez internet
4. ✅ Harmonogram: czas włączenia TV i czas wyświetlania treści

### MAX-imum
- ✅ Wszystko z MIN + integracja z Google Drive (folder ZASTĘPSTWA) - auto-aktualizacja
- ✅ Dzielenie długich plików Excel na grupy monitorów pionowych
- ✅ Graficzna konfiguracja przypisania pięter i rozkładu monitorów
- ✅ Symulacja wyświetlania na stronie informacyjnej (bez logowania)

### Doprecyzowania
- **Chmura**: Google Drive (folder ZASTĘPSTWA)
- **Rozdzielczość**: FHD (1920×1080) telewizory
- **Zarządzanie TV**: Konfigurowalne później (HDMI CEC lub smart plug)
- **Analytics**: NIE (tylko tablice informacyjne)
- **Role**: 
  - **Admin**: Konfiguracja wszystkiego, upload treści (za hasłem)
  - **Operator**: Tylko obserwacja (co się gdzie wyświetla, czy działa)
- **Video**: Transkodowanie na serwerze po uploadzie, klient obsługuje standardowe formaty
- **Monitoring**: Brak komunikacji wyświetlacza widoczny na stronie statusu i raportowany
- **Dzwonki szkolne**: System "przyjaznych dzwonków" z harmonogramem
- **Środowisko**: Hyper-V (serwer na maszynie wirtualnej)

---

## 2. Architektura Systemu - Szczegółowa

### 2.1. Komponenty Systemu

```
┌─────────────────────────────────────────────────────────────┐
│                    SERWER (Ubuntu VM)                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Backend API (FastAPI/Django)                  │  │
│  │  - REST API dla panelu webowego                       │  │
│  │  - WebSocket dla statusu w czasie rzeczywistym        │  │
│  │  - Autentykacja (JWT) - Admin/Operator                │  │
│  │  - Zarządzanie treścią                                │  │
│  │  - Harmonogramy                                        │  │
│  │  - Grupowanie wyświetlaczy                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Panel Webowy (React/Vue.js)                   │  │
│  │  - Dashboard Admin (upload, konfiguracja)             │  │
│  │  - Dashboard Operator (obserwacja, status)            │  │
│  │  - Graficzny edytor układu monitorów                  │  │
│  │  - Symulacja wyświetlania (publiczna, bez logowania)  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Worker (Celery/Bull)                          │  │
│  │  - Transkodowanie video (FFmpeg)                      │  │
│  │  - Przetwarzanie PDF/Excel                            │  │
│  │  - Generowanie miniatur                               │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Google Drive Sync Service                     │  │
│  │  - Monitorowanie folderu ZASTĘPSTWA                   │  │
│  │  - Webhook/polling zmian                              │  │
│  │  - Automatyczne pobieranie i aktualizacja             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Monitoring Service                            │  │
│  │  - Monitorowanie statusu wyświetlaczy                 │  │
│  │  - Wykrywanie braku komunikacji                       │  │
│  │  - Alerty i raporty                                   │  │
│  │  - Historia statusów                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         System Dzwonków Szkolnych                     │  │
│  │  - Harmonogram dzwonków                               │  │
│  │  - Odtwarzanie dźwięków                              │  │
│  │  - Integracja z wyświetlaczami                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Baza Danych (PostgreSQL)                      │  │
│  │  - Wyświetlacze, grupy, treści, harmonogramy         │  │
│  │  - Status wyświetlaczy, alerty                       │  │
│  │  - Harmonogramy dzwonków                             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Storage (lokalny system plików)               │  │
│  │  - /content/original/ - oryginalne pliki             │  │
│  │  - /content/processed/ - przetworzone video          │  │
│  │  - /content/thumbnails/ - miniatury                  │  │
│  │  - /content/cache/ - cache dla wyświetlaczy          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Nginx (serwowanie plików statycznych)         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                    │              │              │
                    │ WiFi         │ WiFi         │ WiFi
                    ▼              ▼              ▼
         ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
         │ Wyświetlacz 1 │  │ Wyświetlacz 2│  │ Wyświetlacz N│
         │ HP T630       │  │ HP T630      │  │ HP T630      │
         │ Linux         │  │ Linux        │  │ Linux        │
         │              │  │              │  │              │
         │ - Klient API  │  │ - Klient API │  │ - Klient API │
         │ - Cache lokal │  │ - Cache lokal│  │ - Cache lokal│
         │ - Player      │  │ - Player     │  │ - Player     │
         │ - Systemd     │  │ - Systemd    │  │ - Systemd    │
         └──────────────┘  └──────────────┘  └──────────────┘
```

---

## 3. Stack Technologiczny - Finalna Propozycja

### 3.1. Backend Serwera

**Główny framework:**
- **Python + FastAPI** (rekomendowane) lub Django
  - Szybki, asynchroniczny
  - Automatyczna dokumentacja API (Swagger)
  - Łatwa integracja z Celery
  - Dobra obsługa WebSocket

**Baza danych:**
- **PostgreSQL 14+**
  - Relacyjna struktura
  - JSONB dla elastycznych konfiguracji
  - Wsparcie dla pełnotekstowego wyszukiwania

**Cache i kolejki:**
- **Redis**
  - Cache sesji
  - Kolejki dla Celery
  - Pub/Sub dla WebSocket

**Przetwarzanie w tle:**
- **Celery** + **Redis** (broker)
  - Transkodowanie video
  - Przetwarzanie plików
  - Synchronizacja z Google Drive

**Przetwarzanie multimedia:**
- **FFmpeg**
  - Transkodowanie video do MP4 (H.264)
  - Optymalizacja dla FHD (1920×1080)
  - Generowanie różnych wersji (jeśli potrzeba)

**Biblioteki Python:**
- `python-multipart` - upload plików
- `Pillow` - przetwarzanie obrazów
- `pdf2image` - konwersja PDF do obrazów
- `openpyxl` / `pandas` - przetwarzanie Excel
- `google-api-python-client` - integracja Google Drive
- `python-jose` - JWT tokens
- `passlib` - hashowanie haseł

### 3.2. Frontend Panelu

**Framework:**
- **React 18+** (rekomendowane) lub Vue 3
  - Duża społeczność
- **TypeScript** - bezpieczeństwo typów

**Biblioteki UI:**
- **Material-UI (MUI)** lub **Ant Design**
  - Gotowe komponenty
  - Responsywność
  - Tematyzacja

**Graficzny edytor układu:**
- **react-grid-layout** lub **react-dnd**
  - Drag & drop
  - Responsywne siatki
  - Zapisywanie konfiguracji

**Komunikacja:**
- **Axios** - HTTP requests
- **Socket.io-client** - WebSocket dla statusu

**Wizualizacja:**
- **react-player** - podgląd video
- **react-pdf** - podgląd PDF
- **Chart.js** - wykresy (jeśli potrzeba)

### 3.3. Klient (Wyświetlacze - HP T630)

**System operacyjny:**
- **Ubuntu 22.04 LTS** lub **Debian 11+**
  - Stabilność
  - Długie wsparcie
  - Łatwa konfiguracja

**Framework wyświetlania:**
- **Python 3.10+**
  - **PyQt6** lub **Kivy**
    - Pełnoekranowy tryb
    - Obsługa rotacji ekranu
    - Dobra wydajność

**Biblioteki Python dla klienta:**
- `requests` - komunikacja z API
- `websocket-client` - WebSocket
- `Pillow` - wyświetlanie obrazów
- `pdf2image` - PDF
- `openpyxl` / `pandas` - Excel
- `vlc-python` lub `mpv` - video
- `pygame` (opcjonalnie) - alternatywa dla prostych animacji

**Zarządzanie procesem:**
- **systemd** - autostart, restart, monitoring
- **cron** - synchronizacja czasu (NTP)

**Obsługa rotacji ekranu:**
- `xrandr` (X11) lub konfiguracja w systemie
- Automatyczna rotacja treści w aplikacji

### 3.4. Integracja Google Drive

**API:**
- **Google Drive API v3**
  - OAuth 2.0 dla autoryzacji
  - Webhook dla zmian (Push notifications)
  - Polling jako fallback

**Biblioteka:**
- `google-api-python-client`
- `google-auth`

**Mechanizm:**
1. Konfiguracja folderu ZASTĘPSTWA w panelu admin
2. Autoryzacja OAuth 2.0 (jednorazowa)
3. Monitorowanie zmian (webhook + polling)
4. Automatyczne pobieranie nowych/zmienionych plików
5. Aktualizacja harmonogramu

### 3.5. Komunikacja

**REST API:**
- Endpointy dla CRUD operacji
- Upload/download plików
- Status wyświetlaczy

**WebSocket:**
- Status w czasie rzeczywistym
- Push aktualizacji treści
- Synchronizacja harmonogramów

**Protokół:**
- HTTPS (TLS 1.3)
- WSS (WebSocket Secure)

---

## 4. Szczegółowa Struktura Bazy Danych

### 4.1. Tabele

```sql
-- Użytkownicy (role: admin, operator)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'operator')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Wyświetlacze
CREATE TABLE displays (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    mac_address VARCHAR(17) UNIQUE NOT NULL,
    ip_address VARCHAR(15),
    status VARCHAR(20) DEFAULT 'offline' CHECK (status IN ('online', 'offline', 'error')),
    orientation INTEGER DEFAULT 0 CHECK (orientation IN (0, 90, 180, 270)),
    resolution_width INTEGER DEFAULT 1920,
    resolution_height INTEGER DEFAULT 1080,
    group_id INTEGER REFERENCES groups(id),
    floor VARCHAR(50),
    position_x INTEGER,  -- Pozycja w graficznym układzie
    position_y INTEGER,
    last_seen TIMESTAMP,
    cache_size_mb INTEGER DEFAULT 1000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grupy wyświetlaczy
CREATE TABLE groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('horizontal', 'vertical', 'mixed', 'single')),
    floor VARCHAR(50),
    layout_config JSONB,  -- Konfiguracja graficznego układu
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Treści
CREATE TABLE content (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('image', 'pdf', 'excel', 'video')),
    file_path VARCHAR(500) NOT NULL,
    thumbnail_path VARCHAR(500),
    video_processed BOOLEAN DEFAULT FALSE,
    video_format VARCHAR(10),  -- mp4, webm, etc.
    file_size_mb DECIMAL(10, 2),
    duration_seconds INTEGER,  -- Dla video
    metadata JSONB,  -- Dodatkowe informacje (rozmiar, kolumny Excel, etc.)
    uploaded_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Harmonogramy
CREATE TABLE schedules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    content_id INTEGER REFERENCES content(id) ON DELETE CASCADE,
    display_id INTEGER REFERENCES displays(id) ON DELETE CASCADE,
    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    start_date DATE,
    end_date DATE,
    days_of_week INTEGER[],  -- [1,2,3,4,5] = pon-pt
    priority INTEGER DEFAULT 0,
    display_duration_seconds INTEGER,  -- Czas wyświetlania treści
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Harmonogramy włączania TV
CREATE TABLE tv_schedules (
    id SERIAL PRIMARY KEY,
    display_id INTEGER REFERENCES displays(id) ON DELETE CASCADE,
    group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,
    power_on_time TIME NOT NULL,
    power_off_time TIME NOT NULL,
    days_of_week INTEGER[],
    active BOOLEAN DEFAULT TRUE,
    control_method VARCHAR(20) CHECK (control_method IN ('hdmi_cec', 'smart_plug', 'manual')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Zadania przetwarzania
CREATE TABLE processing_jobs (
    id SERIAL PRIMARY KEY,
    content_id INTEGER REFERENCES content(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL,  -- 'video_transcode', 'pdf_convert', etc.
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    progress INTEGER DEFAULT 0,  -- 0-100
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Synchronizacja Google Drive
CREATE TABLE cloud_sync (
    id SERIAL PRIMARY KEY,
    folder_id VARCHAR(255) NOT NULL,  -- Google Drive folder ID
    folder_name VARCHAR(255) NOT NULL,
    last_sync_token VARCHAR(255),
    last_sync_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'error')),
    auto_schedule BOOLEAN DEFAULT TRUE,  -- Automatyczne dodawanie do harmonogramu
    config JSONB,  -- Dodatkowa konfiguracja
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pliki z Google Drive
CREATE TABLE cloud_files (
    id SERIAL PRIMARY KEY,
    drive_file_id VARCHAR(255) UNIQUE NOT NULL,
    filename VARCHAR(255) NOT NULL,
    content_id INTEGER REFERENCES content(id) ON DELETE SET NULL,
    sync_id INTEGER REFERENCES cloud_sync(id) ON DELETE CASCADE,
    last_modified_drive TIMESTAMP,
    last_synced_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'synced' CHECK (status IN ('synced', 'pending', 'error')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Logi aktywności (dla operatora)
CREATE TABLE activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),  -- 'content', 'display', 'schedule', etc.
    entity_id INTEGER,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Status wyświetlaczy (cache)
CREATE TABLE display_status (
    display_id INTEGER PRIMARY KEY REFERENCES displays(id) ON DELETE CASCADE,
    current_content_id INTEGER REFERENCES content(id),
    current_schedule_id INTEGER REFERENCES schedules(id),
    cache_status JSONB,  -- Status cache (co jest pobrane, co brakuje)
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Historia statusów wyświetlaczy (dla raportów)
CREATE TABLE display_status_history (
    id SERIAL PRIMARY KEY,
    display_id INTEGER REFERENCES displays(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('online', 'offline', 'error')),
    last_seen TIMESTAMP,
    connection_lost_at TIMESTAMP,  -- Kiedy stracono połączenie
    connection_restored_at TIMESTAMP,  -- Kiedy przywrócono połączenie
    duration_offline_seconds INTEGER,  -- Czas offline w sekundach
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alerty (brak komunikacji, błędy)
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    display_id INTEGER REFERENCES displays(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL CHECK (alert_type IN ('connection_lost', 'connection_restored', 'error', 'cache_missing')),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    message TEXT NOT NULL,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    resolved_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Harmonogramy dzwonków szkolnych
CREATE TABLE bell_schedules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,  -- np. "Dzwonek na lekcję", "Dzwonek na przerwę"
    bell_time TIME NOT NULL,
    days_of_week INTEGER[],  -- [1,2,3,4,5] = pon-pt
    start_date DATE,
    end_date DATE,
    sound_file_path VARCHAR(500),  -- Ścieżka do pliku dźwiękowego
    volume INTEGER DEFAULT 50 CHECK (volume >= 0 AND volume <= 100),
    play_on_displays BOOLEAN DEFAULT TRUE,  -- Czy odtwarzać na wyświetlaczach
    display_ids INTEGER[],  -- Lista ID wyświetlaczy (puste = wszystkie)
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Historia odtworzeń dzwonków
CREATE TABLE bell_history (
    id SERIAL PRIMARY KEY,
    bell_schedule_id INTEGER REFERENCES bell_schedules(id) ON DELETE CASCADE,
    played_at TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'success' CHECK (status IN ('success', 'failed', 'skipped')),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2. Indeksy

```sql
CREATE INDEX idx_displays_group ON displays(group_id);
CREATE INDEX idx_displays_status ON displays(status);
CREATE INDEX idx_schedules_active ON schedules(active) WHERE active = TRUE;
CREATE INDEX idx_schedules_display ON schedules(display_id);
CREATE INDEX idx_schedules_group ON schedules(group_id);
CREATE INDEX idx_schedules_time ON schedules(start_time, end_time);
CREATE INDEX idx_content_type ON content(type);
CREATE INDEX idx_cloud_files_sync ON cloud_files(sync_id);
CREATE INDEX idx_activity_logs_user ON activity_logs(user_id);
CREATE INDEX idx_activity_logs_created ON activity_logs(created_at DESC);
CREATE INDEX idx_display_status_history_display ON display_status_history(display_id);
CREATE INDEX idx_display_status_history_created ON display_status_history(created_at DESC);
CREATE INDEX idx_alerts_display ON alerts(display_id);
CREATE INDEX idx_alerts_resolved ON alerts(resolved) WHERE resolved = FALSE;
CREATE INDEX idx_alerts_created ON alerts(created_at DESC);
CREATE INDEX idx_bell_schedules_active ON bell_schedules(active) WHERE active = TRUE;
CREATE INDEX idx_bell_schedules_time ON bell_schedules(bell_time);
CREATE INDEX idx_bell_history_schedule ON bell_history(bell_schedule_id);
CREATE INDEX idx_bell_history_played ON bell_history(played_at DESC);
```

---

## 5. Szczegółowe Przepływy Działania

### 5.1. Upload Treści (Admin)

1. **Admin loguje się** → JWT token
2. **Upload pliku** → POST `/api/content/upload`
   - Walidacja typu pliku
   - Zapis do `/content/original/`
   - Utworzenie rekordu w `content`
   - Zwrócenie `content_id`
3. **Przetwarzanie w tle** (Celery):
   - **Video**: Transkodowanie do MP4 (H.264, 1920×1080)
   - **PDF**: Generowanie miniatur
   - **Excel**: Analiza struktury (liczba wierszy, kolumn)
   - **Obrazy**: Generowanie miniatur, optymalizacja
4. **Aktualizacja statusu** → `processing_jobs.status = 'completed'`
5. **Gotowe do użycia** → Treść dostępna w harmonogramach

### 5.2. Konfiguracja Grup i Wyświetlaczy (Admin)

1. **Graficzny edytor układu**:
   - Drag & drop wyświetlaczy na wizualizacji budynku
   - Przypisanie do pięter
   - Konfiguracja grup (np. "3 monitory pionowe")
2. **Zapis konfiguracji**:
   - `groups.layout_config` (JSON) - pozycje, rozmiary
   - `displays.group_id`, `displays.floor`, `displays.position_x/y`
3. **Walidacja**:
   - Sprawdzenie czy wyświetlacz nie jest w wielu grupach
   - Sprawdzenie czy grupa ma sens (np. 3 monitory pionowe = 3 wyświetlacze)

### 5.3. Tworzenie Harmonogramu (Admin)

1. **Wybór treści** → Lista dostępnych treści
2. **Wybór wyświetlacza/grupy**:
   - Pojedynczy wyświetlacz
   - Grupa wyświetlaczy
   - Wszystkie wyświetlacze
3. **Konfiguracja czasu**:
   - Czas wyświetlania (start_time, end_time)
   - Daty (start_date, end_date) - opcjonalnie
   - Dni tygodnia
   - Czas wyświetlania treści (display_duration_seconds)
4. **Priorytet** → Jeśli wiele treści w tym samym czasie
5. **Zapis** → `schedules` table
6. **Push do wyświetlaczy** → WebSocket notification

### 5.4. Działanie Wyświetlacza (Klient)

1. **Start systemu** (systemd):
   - Uruchomienie aplikacji klienta
   - Połączenie z serwerem (REST API)
   - Rejestracja wyświetlacza (MAC address)
2. **Pobranie konfiguracji**:
   - GET `/api/displays/{id}/config`
   - Orientacja, rozdzielczość, grupa
3. **Pobranie harmonogramu**:
   - GET `/api/displays/{id}/schedule`
   - Lista treści z czasami
4. **Pobranie treści** (cache):
   - Sprawdzenie co jest w cache lokalnym
   - Pobranie brakujących plików (GET `/api/content/{id}/download`)
   - Zapis do lokalnego cache
5. **Wyświetlanie**:
   - Sprawdzenie aktualnego czasu
   - Wybór treści zgodnie z harmonogramem
   - Wyświetlenie:
     - **Obraz**: Pillow → PyQt6
     - **PDF**: pdf2image → Pillow → PyQt6
     - **Excel**: openpyxl → renderowanie → PyQt6
     - **Video**: VLC/mpv player
6. **Status w czasie rzeczywistym**:
   - WebSocket → wysyłanie statusu co 30s
   - Aktualna treść, status cache, błędy
7. **Obsługa offline**:
   - Jeśli brak połączenia → wyświetlanie z cache
   - Retry połączenia co 60s
   - Queue aktualizacji

### 5.5. Integracja Google Drive (ZASTĘPSTWA)

1. **Konfiguracja** (Admin):
   - Autoryzacja OAuth 2.0 (jednorazowa)
   - Wybór folderu ZASTĘPSTWA
   - Zapis `cloud_sync` record
2. **Monitorowanie zmian**:
   - **Webhook** (preferowane): Google Drive Push notifications
   - **Polling** (fallback): Sprawdzanie co 5 minut
3. **Wykrycie zmiany**:
   - Nowy plik → pobranie → upload do systemu
   - Zmieniony plik → pobranie → aktualizacja
   - Usunięty plik → usunięcie z systemu
4. **Automatyczna aktualizacja harmonogramu**:
   - Jeśli `auto_schedule = TRUE`:
     - Nowy plik → utworzenie harmonogramu (domyślny czas)
     - Zmieniony plik → aktualizacja harmonogramu
5. **Synchronizacja**:
   - Pobranie pliku z Google Drive
   - Upload do systemu (jak normalny upload)
   - Przetwarzanie (transkodowanie, etc.)
   - Aktualizacja `cloud_files` record

### 5.6. Dzielenie Długich Plików Excel

**Algorytm dla grup pionowych (3 monitory obok siebie):**

1. **Analiza pliku Excel**:
   - Liczba wierszy danych
   - Liczba kolumn
   - Rozmiar czcionki (domyślny)
2. **Obliczenie podziału**:
   - Wiersze na monitor = `total_rows / number_of_displays`
   - Dla każdego wyświetlacza: zakres wierszy
3. **Renderowanie**:
   - Dla każdego wyświetlacza:
     - Wyciągnięcie odpowiedniego zakresu wierszy
     - Renderowanie do obrazu (1920×1080, obrócony 90°)
     - Zapis jako osobna "wersja" treści
4. **Przypisanie do harmonogramu**:
   - Ta sama treść, różne "wersje" dla każdego wyświetlacza w grupie
   - Synchronizacja czasu wyświetlania

**Implementacja:**
- `content.metadata` → `{"split_config": {"group_id": 1, "display_index": 0, "row_range": [0, 50]}}`
- Klient pobiera odpowiednią wersję dla swojego wyświetlacza

### 5.7. Symulacja Wyświetlania (Publiczna Strona)

1. **Dostęp bez logowania**:
   - GET `/simulation` (publiczny endpoint)
   - Wyświetlenie wizualizacji wszystkich wyświetlaczy
2. **Wizualizacja**:
   - Graficzny układ monitorów (zgodnie z konfiguracją)
   - Podgląd aktualnie wyświetlanej treści na każdym monitorze
   - Status (online/offline)
3. **Aktualizacja w czasie rzeczywistym**:
   - WebSocket (publiczny, read-only)
   - Aktualizacja co 5-10 sekund
4. **Funkcje**:
   - Przewijanie między piętrami
   - Zoom na konkretny monitor
   - Podgląd harmonogramu

---

## 6. Obsługa Formatów - Szczegóły

### 6.1. PDF

**Przetwarzanie:**
- `pdf2image` → konwersja każdej strony do PNG
- Skalowanie do 1920×1080 (z zachowaniem proporcji)
- Jeśli wiele stron → wybór pierwszej strony lub przewijanie

**Wyświetlanie:**
- Klient: PNG → Pillow → PyQt6
- Pełnoekranowy tryb

### 6.2. Excel

**Przetwarzanie:**
- `openpyxl` → odczyt danych
- Analiza struktury (liczba wierszy, kolumn)
- Dla długich plików → przygotowanie podziału

**Renderowanie:**
- `pandas` + `matplotlib` lub własny renderer
- Skalowanie do 1920×1080
- Automatyczne dopasowanie czcionki
- Dla grup pionowych → podział wierszy

**Wyświetlanie:**
- Obraz PNG → Pillow → PyQt6

### 6.3. Obrazy (JPG, PNG, GIF)

**Przetwarzanie:**
- `Pillow` → optymalizacja, skalowanie
- Dla GIF → konwersja do animacji lub pierwsza klatka

**Wyświetlanie:**
- Pillow → PyQt6
- Pełnoekranowy tryb

### 6.4. Video (MPG → MP4)

**Transkodowanie na serwerze (FFmpeg):**
```bash
ffmpeg -i input.mpg -c:v libx264 -preset medium -crf 23 \
  -c:a aac -b:a 128k -s 1920x1080 -r 30 output.mp4
```

**Parametry:**
- Codec: H.264 (libx264)
- Rozdzielczość: 1920×1080 (FHD)
- Frame rate: 30 fps
- Audio: AAC 128kbps
- CRF: 23 (dobra jakość, rozsądny rozmiar)

**Wyświetlanie:**
- VLC Python bindings lub mpv
- Pełnoekranowy tryb
- Loop (jeśli potrzeba)

---

## 7. Obsługa Rotacji Ekranu (90°)

### 7.1. Poziom Systemu

**Konfiguracja X11 (jeśli X11):**
```bash
xrandr --output HDMI-1 --rotate left  # 90° w lewo
```

**Konfiguracja w aplikacji:**
- `displays.orientation = 90`
- Automatyczna rotacja treści w PyQt6

### 7.2. Poziom Aplikacji

**PyQt6:**
```python
# Rotacja treści
transform = QTransform().rotate(90)
pixmap = pixmap.transformed(transform)
```

**Dla grup pionowych:**
- 3 monitory obok siebie, każdy obrócony 90°
- Treść renderowana z uwzględnieniem rotacji
- Dzielenie Excel z uwzględnieniem rotacji

---

## 8. System Autoryzacji i Ról

### 8.1. Role

**Admin:**
- Wszystkie operacje CRUD
- Upload treści
- Konfiguracja wyświetlaczy i grup
- Tworzenie harmonogramów
- Konfiguracja Google Drive
- Zarządzanie użytkownikami

**Operator:**
- Tylko odczyt (GET)
- Podgląd statusu wyświetlaczy
- Podgląd harmonogramów
- Podgląd treści
- Logi aktywności

### 8.2. Endpointy API

**Admin tylko:**
- POST `/api/content/upload`
- PUT/DELETE `/api/content/{id}`
- POST/PUT/DELETE `/api/displays`
- POST/PUT/DELETE `/api/groups`
- POST/PUT/DELETE `/api/schedules`
- POST `/api/cloud-sync/configure`

**Admin + Operator:**
- GET `/api/content`
- GET `/api/displays`
- GET `/api/groups`
- GET `/api/schedules`
- GET `/api/display-status`
- GET `/api/activity-logs`

**Publiczne:**
- GET `/simulation` (symulacja)

### 8.3. JWT Tokens

- Access token (15 min)
- Refresh token (7 dni)
- Role w payload tokena

---

## 9. Obsługa Błędów i Niezawodność

### 9.1. WiFi - Opóźnienia i Zrywane Połączenia

**Strategia:**
1. **Lokalny cache**:
   - Wszystkie treści w cache lokalnym
   - Minimalna zależność od sieci podczas wyświetlania
2. **Pobieranie w tle**:
   - Pobieranie nowych treści przed czasem wyświetlania
   - Retry z exponential backoff
3. **Status offline**:
   - Wyświetlanie z cache
   - Queue aktualizacji
   - Automatyczne synchronizowanie po powrocie połączenia
4. **Weryfikacja integralności**:
   - Checksum (MD5/SHA256) dla każdego pliku
   - Weryfikacja przy pobieraniu

### 9.2. Przetwarzanie Video - Błędy

**Obsługa:**
- Retry (3 próby)
- Logowanie błędów
- Powiadomienie admina (email/panel)
- Fallback: wyświetlanie oryginalnego pliku (jeśli możliwe)

### 9.3. Synchronizacja Google Drive - Błędy

**Obsługa:**
- Retry z exponential backoff
- Logowanie błędów
- Powiadomienie admina
- Fallback: polling zamiast webhook

---

## 10. Bezpieczeństwo

### 10.1. Serwer

- HTTPS (Let's Encrypt)
- Firewall (UFW)
- Regularne aktualizacje
- Backup bazy danych (codziennie)
- Backup plików (tygodniowo)

### 10.2. Autentykacja

- Silne hasła (min. 12 znaków)
- JWT tokens
- Rate limiting
- CORS configuration

### 10.3. Wyświetlacze

- Autoryzacja przez MAC address
- HTTPS komunikacja
- Read-only dostęp do API (tylko GET dla swoich danych)

---

## 10A. System Monitorowania Statusu Wyświetlaczy

### 10A.1. Mechanizm Wykrywania Braku Komunikacji

**Heartbeat System:**
- Wyświetlacz wysyła status co 30 sekund (WebSocket lub REST API)
- Serwer oczekuje heartbeat w oknie 60 sekund
- Jeśli brak heartbeat przez 60s → status = 'offline'
- Jeśli brak heartbeat przez 5 minut → alert 'connection_lost'

**Endpointy:**
- POST `/api/displays/{id}/heartbeat` - wyświetlacz wysyła status
- GET `/api/displays/{id}/status` - aktualny status
- GET `/api/displays/status/all` - status wszystkich wyświetlaczy

**Dane w heartbeat:**
```json
{
  "display_id": 1,
  "status": "online",
  "current_content_id": 5,
  "cache_status": {
    "total_mb": 1000,
    "used_mb": 500,
    "missing_files": [10, 15]
  },
  "errors": []
}
```

### 10A.2. Strona Statusu (Dashboard)

**Dla Admin i Operator:**
- Lista wszystkich wyświetlaczy z aktualnym statusem
- Wizualizacja:
  - 🟢 Online (zielony)
  - 🔴 Offline (czerwony)
  - 🟡 Error (żółty)
- Czas ostatniego połączenia
- Czas offline (jeśli offline)
- Aktualizacja w czasie rzeczywistym (WebSocket)

**Filtry:**
- Status (online/offline/error)
- Piętro
- Grupa

**Szczegóły wyświetlacza:**
- Historia statusów (ostatnie 24h)
- Aktualna treść
- Status cache
- Błędy

### 10A.3. System Alertów

**Typy alertów:**
1. **connection_lost** - Brak komunikacji > 5 minut
2. **connection_restored** - Przywrócono komunikację
3. **error** - Błąd w działaniu wyświetlacza
4. **cache_missing** - Brakuje plików w cache

**Severity:**
- **critical**: Brak komunikacji > 30 minut
- **error**: Brak komunikacji 5-30 minut, błędy
- **warning**: Brak komunikacji < 5 minut
- **info**: Przywrócono komunikację

**Wyświetlanie alertów:**
- Lista aktywnych alertów na stronie statusu
- Licznik nieprzeczytanych alertów
- Oznaczanie jako przeczytane/rozwiązane

### 10A.4. Raportowanie

**Raporty dostępne dla Admin i Operator:**
1. **Raport dzienny** - Status wyświetlaczy w ciągu dnia
2. **Raport tygodniowy** - Statystyki dostępności
3. **Raport offline** - Czas offline dla każdego wyświetlacza

**Endpointy:**
- GET `/api/reports/daily?date=2024-01-15`
- GET `/api/reports/weekly?week=2024-W03`
- GET `/api/reports/offline?display_id=1&start_date=...&end_date=...`

**Dane w raporcie:**
- Czas online/offline
- Liczba przerw w komunikacji
- Średni czas offline
- Najdłuższy okres offline
- Wykresy dostępności

**Eksport:**
- PDF (dla operatora)
- CSV (dla admina)

---

## 10B. System "Przyjaznych Dzwonków" Szkolnych

### 10B.1. Koncepcja

System odtwarzania dzwonków szkolnych zgodnie z harmonogramem:
- Dzwonek na lekcję
- Dzwonek na przerwę
- Dzwonek na obiad
- Dzwonek na koniec zajęć

**Funkcje:**
- Harmonogramy dla różnych dni tygodnia
- Różne dźwięki dla różnych typów dzwonków
- Odtwarzanie na wyświetlaczach (głośniki wbudowane lub zewnętrzne)
- Możliwość wyłączenia na wybranych wyświetlaczach

### 10B.2. Zarządzanie Dzwonkami (Admin)

**Panel konfiguracji:**
1. **Lista harmonogramów dzwonków**
   - Nazwa (np. "Dzwonek na lekcję - 1")
   - Czas (np. 08:00)
   - Dni tygodnia
   - Plik dźwiękowy
   - Głośność
   - Wyświetlacze (wszystkie lub wybrane)

2. **Upload plików dźwiękowych**
   - Format: MP3, WAV, OGG
   - Walidacja długości (max 30 sekund)
   - Podgląd odtwarzania

3. **Harmonogram tygodniowy**
   - Widok kalendarza z dzwonkami
   - Możliwość kopiowania między dniami
   - Import/export harmonogramu

### 10B.3. Odtwarzanie Dzwonków

**Mechanizm:**
1. **Serwer:**
   - Cron job lub scheduler (Celery Beat)
   - Sprawdzenie harmonogramu co minutę
   - Jeśli czas dzwonka → wysłanie komendy do wyświetlaczy

2. **Wyświetlacze:**
   - Odbieranie komendy przez WebSocket lub REST API
   - Pobranie pliku dźwiękowego (jeśli nie ma w cache)
   - Odtworzenie dźwięku (pygame, vlc-python, lub systemowy player)
   - Logowanie odtworzenia

**Obsługa:**
- Jeśli wyświetlacz offline → pominięcie (logowanie)
- Jeśli brak pliku → próba pobrania, fallback do domyślnego dźwięku
- Jeśli wyświetlacz wyciszony → pominięcie

### 10B.4. Integracja z Wyświetlaczami

**Opcje odtwarzania:**
1. **Na wyświetlaczu** (HP T630):
   - Głośniki wbudowane (jeśli dostępne)
   - Głośniki USB
   - Wyjście audio (3.5mm)

2. **Przez system audio szkoły** (opcjonalnie):
   - Integracja z systemem nagłośnienia
   - API do sterowania

### 10B.5. Historia i Logi

**Tabela `bell_history`:**
- Kiedy odtworzono dzwonek
- Status (sukces/błąd)
- Które wyświetlacze odtworzyły
- Błędy (jeśli wystąpiły)

**Raporty:**
- Statystyki odtworzeń
- Wyświetlacze, które nie odtworzyły
- Częstotliwość błędów

---

## 10C. Środowisko Hyper-V

### 10C.1. Konfiguracja Maszyny Wirtualnej

**Specyfikacje zalecane:**
- **CPU**: 4 vCPU (minimum 2)
- **RAM**: 8 GB (minimum 4 GB)
- **Dysk**: 100 GB (SSD preferowane)
- **Sieć**: Bridge mode (dostęp z sieci lokalnej)

**System operacyjny:**
- Ubuntu Server 22.04 LTS
- Aktualizacje automatyczne (security)

### 10C.2. Konfiguracja Sieci

**Network Adapter:**
- External Virtual Switch (dostęp do sieci WiFi)
- Statyczny IP lub DHCP z rezerwacją
- Port forwarding (jeśli potrzebny dostęp z zewnątrz)

**Firewall:**
- UFW (Uncomplicated Firewall)
- Porty:
  - 80 (HTTP) - przekierowanie do 443
  - 443 (HTTPS)
  - 5432 (PostgreSQL) - tylko lokalnie
  - 6379 (Redis) - tylko lokalnie

### 10C.3. Backup i Odzyskiwanie

**Backup:**
1. **Baza danych** (PostgreSQL):
   - `pg_dump` codziennie (cron)
   - Przechowywanie 30 dni
   - Backup do innej lokalizacji (sieć lokalna)

2. **Pliki treści:**
   - `rsync` tygodniowo
   - Backup do innej lokalizacji

3. **Snapshot Hyper-V:**
   - Przed większymi aktualizacjami
   - Automatyczne snapshoty (opcjonalnie)

**Odzyskiwanie:**
- Procedura przywracania z backupu
- Testowanie backupów (co miesiąc)

### 10C.4. Monitoring Maszyny Wirtualnej

**Metryki:**
- CPU usage
- RAM usage
- Disk usage
- Network traffic
- Uptime

**Alerty:**
- Wysokie użycie zasobów (> 80%)
- Brak miejsca na dysku (< 10%)
- Brak odpowiedzi serwera

---

## 11. Plan Implementacji - Szczegółowy Etapowy

### Etap 0: Przygotowanie Środowiska (1 tydzień)

**Cel:** Przygotowanie infrastruktury i środowiska deweloperskiego

**Zadania:**
1. ✅ Utworzenie maszyny wirtualnej Hyper-V (Ubuntu 22.04)
2. ✅ Konfiguracja sieci (bridge, statyczny IP)
3. ✅ Instalacja podstawowych narzędzi (git, curl, wget)
4. ✅ Instalacja PostgreSQL 14+
5. ✅ Instalacja Redis
6. ✅ Instalacja Python 3.10+ i pip
7. ✅ Instalacja Node.js 18+ (dla frontendu)
8. ✅ Konfiguracja firewall (UFW)
9. ✅ Konfiguracja SSH
10. ✅ Utworzenie użytkownika aplikacji

**Weryfikacja:**
- [ ] VM uruchomiona i dostępna przez SSH
- [ ] PostgreSQL działa (psql --version)
- [ ] Redis działa (redis-cli ping)
- [ ] Python działa (python3 --version)
- [ ] Node.js działa (node --version)
- [ ] Firewall skonfigurowany

**Deliverable:** Działające środowisko deweloperskie

---

### Etap 1: Backend API - Podstawy (1 tydzień)

**Cel:** Utworzenie podstawowej struktury backendu z autentykacją

**Zadania:**
1. ✅ Utworzenie projektu FastAPI
2. ✅ Konfiguracja struktury katalogów
3. ✅ Połączenie z PostgreSQL
4. ✅ Połączenie z Redis
5. ✅ Utworzenie modeli bazy danych (SQLAlchemy)
6. ✅ Migracje bazy danych (Alembic)
7. ✅ System autentykacji (JWT)
8. ✅ Endpointy logowania/logout
9. ✅ Middleware dla autoryzacji (role: admin/operator)
10. ✅ Podstawowe endpointy użytkowników (CRUD)

**Weryfikacja:**
- [ ] API uruchamia się (uvicorn)
- [ ] Połączenie z bazą działa
- [ ] Można się zalogować jako admin
- [ ] Można się zalogować jako operator
- [ ] Role działają poprawnie (admin ma więcej uprawnień)
- [ ] Swagger UI dostępny (/docs)

**Deliverable:** Działające API z autentykacją

**Testy:**
```bash
# Test logowania
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"test123"}'

# Test endpointu chronionego
curl -X GET http://localhost:8000/api/users \
  -H "Authorization: Bearer <token>"
```

---

### Etap 2: Backend - Zarządzanie Wyświetlaczami (3 dni)

**Cel:** CRUD dla wyświetlaczy i podstawowy status

**Zadania:**
1. ✅ Model Display w bazie danych
2. ✅ Endpointy CRUD dla wyświetlaczy (tylko admin)
3. ✅ Endpoint rejestracji wyświetlacza (przez MAC address)
4. ✅ Endpoint heartbeat (POST /api/displays/{id}/heartbeat)
5. ✅ Endpoint statusu (GET /api/displays/{id}/status)
6. ✅ Automatyczne wykrywanie offline (brak heartbeat > 60s)
7. ✅ Tabela display_status_history
8. ✅ Logika aktualizacji statusu

**Weryfikacja:**
- [ ] Można utworzyć wyświetlacz (admin)
- [ ] Można zobaczyć listę wyświetlaczy (admin/operator)
- [ ] Wyświetlacz może się zarejestrować (MAC address)
- [ ] Wyświetlacz może wysyłać heartbeat
- [ ] Status zmienia się na offline po braku heartbeat
- [ ] Historia statusów jest zapisywana

**Deliverable:** System zarządzania wyświetlaczami z podstawowym monitoringiem

---

### Etap 3: Backend - Upload i Przetwarzanie Treści (1 tydzień)

**Cel:** Upload plików i podstawowe przetwarzanie

**Zadania:**
1. ✅ Endpoint upload plików (POST /api/content/upload)
2. ✅ Walidacja typów plików (PDF, Excel, obrazy, video)
3. ✅ Zapis plików do /content/original/
4. ✅ Model Content w bazie danych
5. ✅ Konfiguracja Celery
6. ✅ Worker do przetwarzania obrazów (Pillow)
7. ✅ Worker do przetwarzania PDF (pdf2image)
8. ✅ Worker do przetwarzania Excel (openpyxl)
9. ✅ Generowanie miniatur
10. ✅ Tabela processing_jobs

**Weryfikacja:**
- [ ] Można wgrać obraz (JPG, PNG)
- [ ] Można wgrać PDF
- [ ] Można wgrać Excel
- [ ] Można wgrać video (MPG)
- [ ] Pliki są zapisywane w odpowiednich folderach
- [ ] Miniatury są generowane
- [ ] Status przetwarzania jest widoczny

**Deliverable:** System uploadu i przetwarzania treści

---

### Etap 4: Backend - Transkodowanie Video (3 dni)

**Cel:** Transkodowanie video do MP4 (H.264)

**Zadania:**
1. ✅ Instalacja FFmpeg
2. ✅ Worker do transkodowania video
3. ✅ Konfiguracja parametrów (1920×1080, H.264)
4. ✅ Progress tracking (0-100%)
5. ✅ Obsługa błędów transkodowania
6. ✅ Zapis przetworzonego video do /content/processed/

**Weryfikacja:**
- [ ] Video MPG jest transkodowane do MP4
- [ ] Rozdzielczość to 1920×1080
- [ ] Codec to H.264
- [ ] Progress jest widoczny w API
- [ ] Błędy są logowane

**Deliverable:** System transkodowania video

---

### Etap 5: Backend - Harmonogramy Treści (1 tydzień)

**Cel:** System harmonogramów wyświetlania treści

**Zadania:**
1. ✅ Model Schedule w bazie danych
2. ✅ Endpointy CRUD dla harmonogramów (admin)
3. ✅ Endpoint pobierania harmonogramu dla wyświetlacza
4. ✅ Logika wyboru treści na podstawie czasu
5. ✅ Obsługa dni tygodnia
6. ✅ Obsługa dat (start_date, end_date)
7. ✅ Priorytety harmonogramów
8. ✅ Endpoint GET /api/displays/{id}/schedule

**Weryfikacja:**
- [ ] Można utworzyć harmonogram (admin)
- [ ] Harmonogram ma czas start/end
- [ ] Harmonogram ma dni tygodnia
- [ ] Wyświetlacz może pobrać swój harmonogram
- [ ] Wybór treści działa poprawnie (na podstawie czasu)
- [ ] Priorytety działają

**Deliverable:** System harmonogramów treści

---

### Etap 6: Backend - Grupowanie Wyświetlaczy (3 dni)

**Cel:** System grup wyświetlaczy

**Zadania:**
1. ✅ Model Group w bazie danych
2. ✅ Endpointy CRUD dla grup (admin)
3. ✅ Przypisywanie wyświetlaczy do grup
4. ✅ Typy grup (horizontal, vertical, mixed, single)
5. ✅ Harmonogramy dla grup (zamiast pojedynczych wyświetlaczy)
6. ✅ Endpoint GET /api/groups/{id}/displays

**Weryfikacja:**
- [ ] Można utworzyć grupę (admin)
- [ ] Można przypisać wyświetlacz do grupy
- [ ] Harmonogram może być przypisany do grupy
- [ ] Wszystkie wyświetlacze w grupie otrzymują ten sam harmonogram

**Deliverable:** System grupowania wyświetlaczy

---

### Etap 7: Backend - Monitoring i Alerty (1 tydzień)

**Cel:** System monitorowania statusu i alertów

**Zadania:**
1. ✅ Tabela alerts w bazie danych
2. ✅ Automatyczne tworzenie alertów (connection_lost)
3. ✅ Automatyczne rozwiązywanie alertów (connection_restored)
4. ✅ Endpoint GET /api/alerts (lista alertów)
5. ✅ Endpoint PUT /api/alerts/{id}/resolve (oznaczenie jako rozwiązane)
6. ✅ Endpoint GET /api/displays/status/all (status wszystkich)
7. ✅ Tabela display_status_history
8. ✅ Endpoint GET /api/displays/{id}/status-history

**Weryfikacja:**
- [ ] Alert jest tworzony gdy wyświetlacz traci połączenie > 5 min
- [ ] Alert jest automatycznie rozwiązany gdy połączenie wraca
- [ ] Można zobaczyć listę aktywnych alertów
- [ ] Można oznaczyć alert jako rozwiązany
- [ ] Historia statusów jest zapisywana
- [ ] Można zobaczyć historię statusów wyświetlacza

**Deliverable:** System monitorowania i alertów

---

### Etap 8: Backend - Raportowanie (3 dni)

**Cel:** System raportów statusu wyświetlaczy

**Zadania:**
1. ✅ Endpoint GET /api/reports/daily (raport dzienny)
2. ✅ Endpoint GET /api/reports/weekly (raport tygodniowy)
3. ✅ Endpoint GET /api/reports/offline (raport offline)
4. ✅ Obliczanie statystyk (czas online/offline)
5. ✅ Eksport do CSV (dla admina)
6. ✅ Eksport do PDF (dla operatora) - opcjonalnie

**Weryfikacja:**
- [ ] Raport dzienny pokazuje statystyki dla dnia
- [ ] Raport tygodniowy pokazuje statystyki dla tygodnia
- [ ] Raport offline pokazuje czas offline dla wyświetlacza
- [ ] Eksport CSV działa
- [ ] Dane w raportach są poprawne

**Deliverable:** System raportowania

---

### Etap 9: Backend - System Dzwonków (1 tydzień)

**Cel:** System harmonogramów i odtwarzania dzwonków szkolnych

**Zadania:**
1. ✅ Tabela bell_schedules w bazie danych
2. ✅ Endpointy CRUD dla harmonogramów dzwonków (admin)
3. ✅ Upload plików dźwiękowych
4. ✅ Konfiguracja Celery Beat (scheduler)
5. ✅ Task do sprawdzania harmonogramu dzwonków (co minutę)
6. ✅ Endpoint POST /api/displays/{id}/play-bell (odtwarzanie dzwonka)
7. ✅ Tabela bell_history
8. ✅ Logowanie odtworzeń dzwonków

**Weryfikacja:**
- [ ] Można utworzyć harmonogram dzwonka (admin)
- [ ] Można wgrać plik dźwiękowy
- [ ] Scheduler sprawdza harmonogram co minutę
- [ ] Komenda odtwarzania jest wysyłana do wyświetlaczy
- [ ] Historia odtworzeń jest zapisywana

**Deliverable:** System dzwonków szkolnych (backend)

---

### Etap 10: Frontend - Podstawowa Struktura (1 tydzień)

**Cel:** Utworzenie podstawowej struktury frontendu

**Zadania:**
1. ✅ Utworzenie projektu React + TypeScript
2. ✅ Konfiguracja routing (React Router)
3. ✅ Konfiguracja Axios (HTTP client)
4. ✅ Konfiguracja WebSocket (Socket.io-client)
5. ✅ Strona logowania
6. ✅ Layout główny (sidebar, header)
7. ✅ Dashboard (podstawowy)
8. ✅ Integracja z backendem (logowanie)

**Weryfikacja:**
- [ ] Aplikacja się uruchamia (npm start)
- [ ] Można się zalogować
- [ ] Routing działa
- [ ] Połączenie z API działa
- [ ] Layout jest responsywny

**Deliverable:** Działający frontend z logowaniem

---

### Etap 11: Frontend - Zarządzanie Wyświetlaczami (1 tydzień)

**Cel:** Panel do zarządzania wyświetlaczami

**Zadania:**
1. ✅ Lista wyświetlaczy (tabela)
2. ✅ Formularz dodawania/edycji wyświetlacza (admin)
3. ✅ Usuwanie wyświetlacza (admin)
4. ✅ Szczegóły wyświetlacza
5. ✅ Status wyświetlacza (online/offline) z kolorem
6. ✅ Historia statusów (wykres)
7. ✅ Filtry (status, piętro, grupa)

**Weryfikacja:**
- [ ] Lista wyświetlaczy się wyświetla
- [ ] Można dodać wyświetlacz (admin)
- [ ] Można edytować wyświetlacz (admin)
- [ ] Można usunąć wyświetlacz (admin)
- [ ] Status jest widoczny z kolorem
- [ ] Historia statusów jest widoczna

**Deliverable:** Panel zarządzania wyświetlaczami

---

### Etap 12: Frontend - Strona Statusu (1 tydzień)

**Cel:** Strona statusu z monitoringiem w czasie rzeczywistym

**Zadania:**
1. ✅ Strona statusu wszystkich wyświetlaczy
2. ✅ Wizualizacja statusu (kolorowe ikony)
3. ✅ WebSocket dla aktualizacji w czasie rzeczywistym
4. ✅ Lista aktywnych alertów
5. ✅ Szczegóły wyświetlacza (modal)
6. ✅ Filtry i sortowanie
7. ✅ Odświeżanie automatyczne

**Weryfikacja:**
- [ ] Strona statusu wyświetla wszystkie wyświetlacze
- [ ] Status jest aktualizowany w czasie rzeczywistym
- [ ] Alerty są widoczne
- [ ] Można zobaczyć szczegóły wyświetlacza
- [ ] Filtry działają

**Deliverable:** Strona statusu z monitoringiem

---

### Etap 13: Frontend - Upload Treści (1 tydzień)

**Cel:** Panel do uploadu i zarządzania treścią

**Zadania:**
1. ✅ Lista treści (tabela z miniaturami)
2. ✅ Formularz upload (drag & drop)
3. ✅ Progress bar podczas uploadu
4. ✅ Status przetwarzania (pending/processing/completed)
5. ✅ Podgląd treści (obrazy, PDF, video)
6. ✅ Usuwanie treści (admin)
7. ✅ Filtry (typ, status)

**Weryfikacja:**
- [ ] Można wgrać plik (drag & drop)
- [ ] Progress bar działa
- [ ] Status przetwarzania jest widoczny
- [ ] Można zobaczyć podgląd treści
- [ ] Można usunąć treść (admin)

**Deliverable:** Panel uploadu i zarządzania treścią

---

### Etap 14: Frontend - Harmonogramy (1 tydzień)

**Cel:** Panel do zarządzania harmonogramami

**Zadania:**
1. ✅ Lista harmonogramów
2. ✅ Formularz tworzenia/edycji harmonogramu
3. ✅ Wybór treści (dropdown)
4. ✅ Wybór wyświetlacza/grupy
5. ✅ Konfiguracja czasu (start/end)
6. ✅ Konfiguracja dni tygodnia
7. ✅ Konfiguracja dat (start/end)
8. ✅ Priorytety
9. ✅ Kalendarz harmonogramów

**Weryfikacja:**
- [ ] Można utworzyć harmonogram (admin)
- [ ] Można edytować harmonogram (admin)
- [ ] Można usunąć harmonogram (admin)
- [ ] Kalendarz pokazuje harmonogramy
- [ ] Wszystkie opcje konfiguracji działają

**Deliverable:** Panel zarządzania harmonogramami

---

### Etap 15: Frontend - Raporty (3 dni)

**Cel:** Panel raportów

**Zadania:**
1. ✅ Strona raportów
2. ✅ Formularz wyboru zakresu dat
3. ✅ Raport dzienny (tabela + wykres)
4. ✅ Raport tygodniowy (tabela + wykres)
5. ✅ Raport offline (tabela)
6. ✅ Eksport do CSV
7. ✅ Eksport do PDF (opcjonalnie)

**Weryfikacja:**
- [ ] Raporty się generują
- [ ] Wykresy są czytelne
- [ ] Eksport CSV działa
- [ ] Dane w raportach są poprawne

**Deliverable:** Panel raportów

---

### Etap 16: Frontend - System Dzwonków (1 tydzień)

**Cel:** Panel zarządzania dzwonkami szkolnymi

**Zadania:**
1. ✅ Lista harmonogramów dzwonków
2. ✅ Formularz tworzenia/edycji harmonogramu dzwonka
3. ✅ Upload plików dźwiękowych
4. ✅ Podgląd odtwarzania dźwięku
5. ✅ Konfiguracja głośności
6. ✅ Wybór wyświetlaczy
7. ✅ Kalendarz dzwonków
8. ✅ Historia odtworzeń

**Weryfikacja:**
- [ ] Można utworzyć harmonogram dzwonka (admin)
- [ ] Można wgrać plik dźwiękowy
- [ ] Można odsłuchać dźwięk
- [ ] Kalendarz pokazuje dzwonki
- [ ] Historia odtworzeń jest widoczna

**Deliverable:** Panel zarządzania dzwonkami

---

### Etap 17: Klient - Podstawowa Aplikacja (1 tydzień)

**Cel:** Podstawowa aplikacja klienta na wyświetlaczu

**Zadania:**
1. ✅ Utworzenie aplikacji Python + PyQt6
2. ✅ Pełnoekranowy tryb
3. ✅ Połączenie z API (REST)
4. ✅ Rejestracja wyświetlacza (MAC address)
5. ✅ Pobieranie konfiguracji
6. ✅ Pobieranie harmonogramu
7. ✅ Podstawowe wyświetlanie obrazu
8. ✅ Systemd service (autostart)

**Weryfikacja:**
- [ ] Aplikacja uruchamia się
- [ ] Aplikacja łączy się z serwerem
- [ ] Wyświetlacz rejestruje się
- [ ] Aplikacja pobiera harmonogram
- [ ] Obraz jest wyświetlany pełnoekranowo
- [ ] Aplikacja startuje automatycznie (systemd)

**Deliverable:** Podstawowa aplikacja klienta

---

### Etap 18: Klient - Wyświetlanie Formatów (1 tydzień)

**Cel:** Obsługa wszystkich formatów treści

**Zadania:**
1. ✅ Wyświetlanie obrazów (JPG, PNG)
2. ✅ Wyświetlanie PDF (pdf2image)
3. ✅ Wyświetlanie Excel (openpyxl + renderowanie)
4. ✅ Wyświetlanie video (VLC/mpv)
5. ✅ Skalowanie do 1920×1080
6. ✅ Obsługa rotacji 90°
7. ✅ Przełączanie treści zgodnie z harmonogramem

**Weryfikacja:**
- [ ] Obrazy są wyświetlane poprawnie
- [ ] PDF jest wyświetlany (pierwsza strona)
- [ ] Excel jest wyświetlany (renderowany)
- [ ] Video jest odtwarzane
- [ ] Rotacja 90° działa
- [ ] Przełączanie treści działa zgodnie z harmonogramem

**Deliverable:** Klient z pełną obsługą formatów

---

### Etap 19: Klient - Cache i Offline (1 tydzień)

**Cel:** System cache i obsługa offline

**Zadania:**
1. ✅ Lokalny cache plików (/cache/)
2. ✅ Pobieranie treści w tle
3. ✅ Weryfikacja checksum (integralność)
4. ✅ Obsługa offline (wyświetlanie z cache)
5. ✅ Retry połączenia (exponential backoff)
6. ✅ Queue aktualizacji
7. ✅ Status cache (co jest, czego brakuje)
8. ✅ Heartbeat (co 30s)

**Weryfikacja:**
- [ ] Pliki są cache'owane lokalnie
- [ ] Pobieranie w tle działa
- [ ] Wyświetlanie z cache działa (offline)
- [ ] Retry działa po powrocie połączenia
- [ ] Heartbeat jest wysyłany
- [ ] Status cache jest raportowany

**Deliverable:** Klient z cache i obsługą offline

---

### Etap 20: Klient - Dzwonki (3 dni)

**Cel:** Odtwarzanie dzwonków na wyświetlaczu

**Zadania:**
1. ✅ Odbieranie komendy odtwarzania dzwonka (WebSocket/REST)
2. ✅ Pobieranie pliku dźwiękowego (jeśli brakuje)
3. ✅ Odtwarzanie dźwięku (pygame/vlc)
4. ✅ Konfiguracja głośności
5. ✅ Logowanie odtworzenia
6. ✅ Obsługa błędów (brak pliku, brak audio)

**Weryfikacja:**
- [ ] Dzwonek jest odtwarzany o właściwym czasie
- [ ] Głośność jest poprawna
- [ ] Błędy są obsługiwane
- [ ] Logowanie działa

**Deliverable:** Klient z obsługą dzwonków

---

### Etap 21: Integracja Google Drive (1 tydzień)

**Cel:** Integracja z Google Drive (folder ZASTĘPSTWA)

**Zadania:**
1. ✅ Konfiguracja OAuth 2.0 (Google)
2. ✅ Endpoint autoryzacji
3. ✅ Wybór folderu ZASTĘPSTWA
4. ✅ Monitorowanie zmian (webhook + polling)
5. ✅ Automatyczne pobieranie plików
6. ✅ Upload do systemu
7. ✅ Automatyczne tworzenie harmonogramów (opcjonalnie)
8. ✅ Tabela cloud_sync i cloud_files

**Weryfikacja:**
- [ ] Można autoryzować Google Drive (admin)
- [ ] Można wybrać folder ZASTĘPSTWA
- [ ] Zmiany są wykrywane
- [ ] Pliki są automatycznie pobierane
- [ ] Pliki są uploadowane do systemu

**Deliverable:** Integracja Google Drive

---

### Etap 22: Dzielenie Długich Excel (1 tydzień)

**Cel:** Dzielenie długich plików Excel na grupy monitorów pionowych

**Zadania:**
1. ✅ Analiza pliku Excel (liczba wierszy)
2. ✅ Algorytm podziału wierszy
3. ✅ Renderowanie części dla każdego wyświetlacza
4. ✅ Zapis jako osobne "wersje" treści
5. ✅ Metadata z konfiguracją podziału
6. ✅ Klient pobiera odpowiednią wersję

**Weryfikacja:**
- [ ] Długi Excel jest analizowany
- [ ] Podział na części działa
- [ ] Każdy wyświetlacz w grupie otrzymuje swoją część
- [ ] Renderowanie działa poprawnie
- [ ] Klient wyświetla właściwą część

**Deliverable:** System dzielenia długich Excel

---

### Etap 23: Graficzny Edytor Układu (1 tydzień)

**Cel:** Graficzny edytor układu monitorów

**Zadania:**
1. ✅ Wizualizacja budynku (piętra)
2. ✅ Drag & drop wyświetlaczy
3. ✅ Konfiguracja pozycji (x, y)
4. ✅ Konfiguracja grup (pionowe 3x)
5. ✅ Zapis konfiguracji (JSON)
6. ✅ Walidacja układu

**Weryfikacja:**
- [ ] Można przeciągnąć wyświetlacz na wizualizację
- [ ] Pozycja jest zapisywana
- [ ] Grupy są konfigurowane
- [ ] Konfiguracja jest zapisywana

**Deliverable:** Graficzny edytor układu

---

### Etap 24: Symulacja Wyświetlania (1 tydzień)

**Cel:** Publiczna strona symulacji wyświetlania

**Zadania:**
1. ✅ Publiczna strona /simulation (bez logowania)
2. ✅ Wizualizacja wszystkich wyświetlaczy
3. ✅ Podgląd aktualnej treści na każdym monitorze
4. ✅ Status online/offline
5. ✅ WebSocket dla aktualizacji (publiczny, read-only)
6. ✅ Przewijanie między piętrami
7. ✅ Zoom na monitor

**Weryfikacja:**
- [ ] Strona jest dostępna bez logowania
- [ ] Wizualizacja pokazuje wszystkie wyświetlacze
- [ ] Podgląd treści działa
- [ ] Status jest aktualizowany w czasie rzeczywistym
- [ ] Przewijanie i zoom działają

**Deliverable:** Publiczna strona symulacji

---

### Etap 25: Testy i Optymalizacja (1 tydzień)

**Cel:** Testy całego systemu i optymalizacja

**Zadania:**
1. ✅ Testy integracyjne
2. ✅ Testy wydajnościowe
3. ✅ Testy obciążeniowe (10 wyświetlaczy)
4. ✅ Optymalizacja zapytań do bazy
5. ✅ Optymalizacja cache
6. ✅ Naprawa błędów
7. ✅ Dokumentacja użytkownika

**Weryfikacja:**
- [ ] Wszystkie funkcje działają
- [ ] System obsługuje 10 wyświetlaczy
- [ ] Wydajność jest akceptowalna
- [ ] Błędy są naprawione
- [ ] Dokumentacja jest kompletna

**Deliverable:** Gotowy system do wdrożenia

---

## 12. Harmonogram Implementacji (Szacunkowy)

| Etap | Nazwa | Czas | Zależności |
|------|-------|------|------------|
| 0 | Przygotowanie środowiska | 1 tydzień | - |
| 1 | Backend API - Podstawy | 1 tydzień | 0 |
| 2 | Backend - Wyświetlacze | 3 dni | 1 |
| 3 | Backend - Upload treści | 1 tydzień | 1 |
| 4 | Backend - Transkodowanie video | 3 dni | 3 |
| 5 | Backend - Harmonogramy | 1 tydzień | 3 |
| 6 | Backend - Grupowanie | 3 dni | 2, 5 |
| 7 | Backend - Monitoring | 1 tydzień | 2 |
| 8 | Backend - Raportowanie | 3 dni | 7 |
| 9 | Backend - Dzwonki | 1 tydzień | 1 |
| 10 | Frontend - Podstawy | 1 tydzień | 1 |
| 11 | Frontend - Wyświetlacze | 1 tydzień | 10, 2 |
| 12 | Frontend - Status | 1 tydzień | 10, 7 |
| 13 | Frontend - Upload | 1 tydzień | 10, 3 |
| 14 | Frontend - Harmonogramy | 1 tydzień | 10, 5 |
| 15 | Frontend - Raporty | 3 dni | 10, 8 |
| 16 | Frontend - Dzwonki | 1 tydzień | 10, 9 |
| 17 | Klient - Podstawy | 1 tydzień | 1, 2 |
| 18 | Klient - Formaty | 1 tydzień | 17, 3 |
| 19 | Klient - Cache | 1 tydzień | 17, 5 |
| 20 | Klient - Dzwonki | 3 dni | 17, 9 |
| 21 | Google Drive | 1 tydzień | 3 |
| 22 | Dzielenie Excel | 1 tydzień | 3, 6 |
| 23 | Edytor układu | 1 tydzień | 10, 6 |
| 24 | Symulacja | 1 tydzień | 10, 12 |
| 25 | Testy i optymalizacja | 1 tydzień | Wszystkie |

**Całkowity czas:** ~20-22 tygodni (5-6 miesięcy)

**Możliwość równoległej pracy:**
- Etapy 10-16 (Frontend) mogą być równoległe z 17-20 (Klient)
- Etapy 21-24 mogą być równoległe

---

## 13. Metodyka Weryfikacji Etapów

### Dla każdego etapu:

1. **Checklist weryfikacji** - lista punktów do sprawdzenia
2. **Testy manualne** - scenariusze testowe
3. **Testy API** - curl/Postman
4. **Testy integracyjne** - połączenie komponentów
5. **Code review** - przegląd kodu

### Przykładowy proces weryfikacji:

1. **Przygotowanie:**
   - Sprawdzenie czy wszystkie zależności są spełnione
   - Przygotowanie środowiska testowego

2. **Testy funkcjonalne:**
   - Wykonanie wszystkich scenariuszy z checklist
   - Sprawdzenie czy wszystkie funkcje działają

3. **Testy niefunkcjonalne:**
   - Wydajność
   - Bezpieczeństwo
   - Obsługa błędów

4. **Dokumentacja:**
   - Aktualizacja dokumentacji
   - Notatki z testów

5. **Zatwierdzenie:**
   - Zatwierdzenie przez zespół
   - Przejście do następnego etapu

---

**Gotowe do implementacji etapowej!** 🚀

### Faza 1: MVP (MIN-imum)
1. Backend API (FastAPI)
2. Baza danych (PostgreSQL)
3. Panel webowy (React) - podstawowy
4. Upload treści (PDF, Excel, obrazy, video)
5. Transkodowanie video (FFmpeg)
6. Klient wyświetlacza (Python + PyQt6)
7. Podstawowe harmonogramy
8. Grupowanie wyświetlaczy (proste)
9. Obsługa rotacji 90°

**Czas: ~6-8 tygodni**

### Faza 2: Rozszerzenia
1. Integracja Google Drive
2. Dzielenie długich plików Excel
3. Graficzny edytor układu
4. Symulacja wyświetlania
5. Harmonogramy włączania TV (podstawowe)
6. WebSocket dla statusu w czasie rzeczywistym

**Czas: ~4-6 tygodni**

### Faza 3: Optymalizacja i Polishing
1. Zaawansowane harmonogramy TV
2. Optymalizacja cache
3. Monitoring i alerty
4. Dokumentacja
5. Testy

**Czas: ~2-3 tygodnie**

---

## 12. Pytania i Uwagi

### Do doprecyzowania:
1. **Harmonogramy TV**: Czy potrzebne różne czasy dla różnych dni tygodnia? (np. weekendy)
2. **Dzielenie Excel**: Czy zawsze dzielić równo, czy możliwość ręcznej konfiguracji zakresów?
3. **Video**: Czy potrzebne różne wersje jakościowe dla różnych wyświetlaczy?
4. **Backup**: Jak często i gdzie przechowywać?
5. **Monitoring**: Czy potrzebne powiadomienia email/SMS przy błędach?

### Zalecenia:
- Rozpoczęcie od MVP (Faza 1)
- Testowanie na 1-2 wyświetlaczach przed pełnym wdrożeniem
- Dokumentacja dla operatora (jak używać panelu)
- Backup przed każdą większą zmianą

---

## 13. Podsumowanie Technologii

| Komponent | Technologia |
|-----------|-------------|
| Backend | Python + FastAPI |
| Frontend | React + TypeScript |
| Baza danych | PostgreSQL |
| Cache/Kolejki | Redis |
| Worker | Celery |
| Multimedia | FFmpeg, Pillow, pdf2image, openpyxl |
| Klient | Python + PyQt6 |
| Video player | VLC Python / mpv |
| Google Drive | google-api-python-client |
| WebSocket | Socket.io / FastAPI WebSocket |
| Serwer plików | Nginx |
| System klienta | Ubuntu/Debian + systemd |

---

**Gotowe do implementacji!** 🚀

