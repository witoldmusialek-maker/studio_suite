# Analiza Systemu Studio Suite - SzczegĂłĹ‚owa Specyfikacja

## 1. Wymagania Funkcjonalne - Aktualizacja

### MIN-imum
1. âś… WyĹ›wietlanie: Excel, PDF (skalowanie na jednÄ… stronÄ™), MPG, JPG
2. âś… ObrĂłt 90Â° (3 monitory pionowe obok siebie)
3. âś… RĂłwnolegĹ‚e/osobne wyĹ›wietlanie na 4 TV (2Ă— 1 piÄ™tro, 1Ă— parter, 1Ă— 2 piÄ™tro) przez internet
4. âś… Harmonogram: czas wĹ‚Ä…czenia TV i czas wyĹ›wietlania treĹ›ci

### MAX-imum
- âś… Wszystko z MIN + integracja z Google Drive (folder ZASTÄPSTWA) - auto-aktualizacja
- âś… Dzielenie dĹ‚ugich plikĂłw Excel na grupy monitorĂłw pionowych
- âś… Graficzna konfiguracja przypisania piÄ™ter i rozkĹ‚adu monitorĂłw
- âś… Symulacja wyĹ›wietlania na stronie informacyjnej (bez logowania)

### Doprecyzowania
- **Chmura**: Google Drive (folder ZASTÄPSTWA)
- **RozdzielczoĹ›Ä‡**: FHD (1920Ă—1080) telewizory
- **ZarzÄ…dzanie TV**: Konfigurowalne pĂłĹşniej (HDMI CEC lub smart plug)
- **Analytics**: NIE (tylko tablice informacyjne)
- **Role**: 
  - **Admin**: Konfiguracja wszystkiego, upload treĹ›ci (za hasĹ‚em)
  - **Operator**: Tylko obserwacja (co siÄ™ gdzie wyĹ›wietla, czy dziaĹ‚a)
- **Video**: Transkodowanie na serwerze po uploadzie, klient obsĹ‚uguje standardowe formaty
- **Monitoring**: Brak komunikacji wyĹ›wietlacza widoczny na stronie statusu i raportowany
- **Dzwonki szkolne**: System "przyjaznych dzwonkĂłw" z harmonogramem
- **Ĺšrodowisko**: Hyper-V (serwer na maszynie wirtualnej)

---

## 2. Architektura Systemu - SzczegĂłĹ‚owa

### 2.1. Komponenty Systemu

```
â”Śâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    SERWER (Ubuntu VM)                        â”‚
â”‚                                                              â”‚
â”‚  â”Śâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚  â”‚         Backend API (FastAPI/Django)                  â”‚  â”‚
â”‚  â”‚  - REST API dla panelu webowego                       â”‚  â”‚
â”‚  â”‚  - WebSocket dla statusu w czasie rzeczywistym        â”‚  â”‚
â”‚  â”‚  - Autentykacja (JWT) - Admin/Operator                â”‚  â”‚
â”‚  â”‚  - ZarzÄ…dzanie treĹ›ciÄ…                                â”‚  â”‚
â”‚  â”‚  - Harmonogramy                                        â”‚  â”‚
â”‚  â”‚  - Grupowanie wyĹ›wietlaczy                            â”‚  â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚                                                              â”‚
â”‚  â”Śâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚  â”‚         Panel Webowy (React/Vue.js)                   â”‚  â”‚
â”‚  â”‚  - Dashboard Admin (upload, konfiguracja)             â”‚  â”‚
â”‚  â”‚  - Dashboard Operator (obserwacja, status)            â”‚  â”‚
â”‚  â”‚  - Graficzny edytor ukĹ‚adu monitorĂłw                  â”‚  â”‚
â”‚  â”‚  - Symulacja wyĹ›wietlania (publiczna, bez logowania)  â”‚  â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚                                                              â”‚
â”‚  â”Śâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚  â”‚         Worker (Celery/Bull)                          â”‚  â”‚
â”‚  â”‚  - Transkodowanie video (FFmpeg)                      â”‚  â”‚
â”‚  â”‚  - Przetwarzanie PDF/Excel                            â”‚  â”‚
â”‚  â”‚  - Generowanie miniatur                               â”‚  â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚                                                              â”‚
â”‚  â”Śâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚  â”‚         Google Drive Sync Service                     â”‚  â”‚
â”‚  â”‚  - Monitorowanie folderu ZASTÄPSTWA                   â”‚  â”‚
â”‚  â”‚  - Webhook/polling zmian                              â”‚  â”‚
â”‚  â”‚  - Automatyczne pobieranie i aktualizacja             â”‚  â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚                                                              â”‚
â”‚  â”Śâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚  â”‚         Monitoring Service                            â”‚  â”‚
â”‚  â”‚  - Monitorowanie statusu wyĹ›wietlaczy                 â”‚  â”‚
â”‚  â”‚  - Wykrywanie braku komunikacji                       â”‚  â”‚
â”‚  â”‚  - Alerty i raporty                                   â”‚  â”‚
â”‚  â”‚  - Historia statusĂłw                                  â”‚  â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚                                                              â”‚
â”‚  â”Śâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚  â”‚         System DzwonkĂłw Szkolnych                     â”‚  â”‚
â”‚  â”‚  - Harmonogram dzwonkĂłw                               â”‚  â”‚
â”‚  â”‚  - Odtwarzanie dĹşwiÄ™kĂłw                              â”‚  â”‚
â”‚  â”‚  - Integracja z wyĹ›wietlaczami                       â”‚  â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚                                                              â”‚
â”‚  â”Śâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚  â”‚         Baza Danych (PostgreSQL)                      â”‚  â”‚
â”‚  â”‚  - WyĹ›wietlacze, grupy, treĹ›ci, harmonogramy         â”‚  â”‚
â”‚  â”‚  - Status wyĹ›wietlaczy, alerty                       â”‚  â”‚
â”‚  â”‚  - Harmonogramy dzwonkĂłw                             â”‚  â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚                                                              â”‚
â”‚  â”Śâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚  â”‚         Storage (lokalny system plikĂłw)               â”‚  â”‚
â”‚  â”‚  - /content/original/ - oryginalne pliki             â”‚  â”‚
â”‚  â”‚  - /content/processed/ - przetworzone video          â”‚  â”‚
â”‚  â”‚  - /content/thumbnails/ - miniatury                  â”‚  â”‚
â”‚  â”‚  - /content/cache/ - cache dla wyĹ›wietlaczy          â”‚  â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚                                                              â”‚
â”‚  â”Śâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â”‚  â”‚         Nginx (serwowanie plikĂłw statycznych)         â”‚  â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                    â”‚              â”‚              â”‚
                    â”‚ WiFi         â”‚ WiFi         â”‚ WiFi
                    â–Ľ              â–Ľ              â–Ľ
         â”Śâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Śâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Śâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
         â”‚ WyĹ›wietlacz 1 â”‚  â”‚ WyĹ›wietlacz 2â”‚  â”‚ WyĹ›wietlacz Nâ”‚
         â”‚ HP T630       â”‚  â”‚ HP T630      â”‚  â”‚ HP T630      â”‚
         â”‚ Linux         â”‚  â”‚ Linux        â”‚  â”‚ Linux        â”‚
         â”‚              â”‚  â”‚              â”‚  â”‚              â”‚
         â”‚ - Klient API  â”‚  â”‚ - Klient API â”‚  â”‚ - Klient API â”‚
         â”‚ - Cache lokal â”‚  â”‚ - Cache lokalâ”‚  â”‚ - Cache lokalâ”‚
         â”‚ - Player      â”‚  â”‚ - Player     â”‚  â”‚ - Player     â”‚
         â”‚ - Systemd     â”‚  â”‚ - Systemd    â”‚  â”‚ - Systemd    â”‚
         â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
```

---

## 3. Stack Technologiczny - Finalna Propozycja

### 3.1. Backend Serwera

**GĹ‚Ăłwny framework:**
- **Python + FastAPI** (rekomendowane) lub Django
  - Szybki, asynchroniczny
  - Automatyczna dokumentacja API (Swagger)
  - Ĺatwa integracja z Celery
  - Dobra obsĹ‚uga WebSocket

**Baza danych:**
- **PostgreSQL 14+**
  - Relacyjna struktura
  - JSONB dla elastycznych konfiguracji
  - Wsparcie dla peĹ‚notekstowego wyszukiwania

**Cache i kolejki:**
- **Redis**
  - Cache sesji
  - Kolejki dla Celery
  - Pub/Sub dla WebSocket

**Przetwarzanie w tle:**
- **Celery** + **Redis** (broker)
  - Transkodowanie video
  - Przetwarzanie plikĂłw
  - Synchronizacja z Google Drive

**Przetwarzanie multimedia:**
- **FFmpeg**
  - Transkodowanie video do MP4 (H.264)
  - Optymalizacja dla FHD (1920Ă—1080)
  - Generowanie rĂłĹĽnych wersji (jeĹ›li potrzeba)

**Biblioteki Python:**
- `python-multipart` - upload plikĂłw
- `Pillow` - przetwarzanie obrazĂłw
- `pdf2image` - konwersja PDF do obrazĂłw
- `openpyxl` / `pandas` - przetwarzanie Excel
- `google-api-python-client` - integracja Google Drive
- `python-jose` - JWT tokens
- `passlib` - hashowanie haseĹ‚

### 3.2. Frontend Panelu

**Framework:**
- **React 18+** (rekomendowane) lub Vue 3
  - DuĹĽa spoĹ‚ecznoĹ›Ä‡
- **TypeScript** - bezpieczeĹ„stwo typĂłw

**Biblioteki UI:**
- **Material-UI (MUI)** lub **Ant Design**
  - Gotowe komponenty
  - ResponsywnoĹ›Ä‡
  - Tematyzacja

**Graficzny edytor ukĹ‚adu:**
- **react-grid-layout** lub **react-dnd**
  - Drag & drop
  - Responsywne siatki
  - Zapisywanie konfiguracji

**Komunikacja:**
- **Axios** - HTTP requests
- **Socket.io-client** - WebSocket dla statusu

**Wizualizacja:**
- **react-player** - podglÄ…d video
- **react-pdf** - podglÄ…d PDF
- **Chart.js** - wykresy (jeĹ›li potrzeba)

### 3.3. Klient (WyĹ›wietlacze - HP T630)

**System operacyjny:**
- **Ubuntu 22.04 LTS** lub **Debian 11+**
  - StabilnoĹ›Ä‡
  - DĹ‚ugie wsparcie
  - Ĺatwa konfiguracja

**Framework wyĹ›wietlania:**
- **Python 3.10+**
  - **PyQt6** lub **Kivy**
    - PeĹ‚noekranowy tryb
    - ObsĹ‚uga rotacji ekranu
    - Dobra wydajnoĹ›Ä‡

**Biblioteki Python dla klienta:**
- `requests` - komunikacja z API
- `websocket-client` - WebSocket
- `Pillow` - wyĹ›wietlanie obrazĂłw
- `pdf2image` - PDF
- `openpyxl` / `pandas` - Excel
- `vlc-python` lub `mpv` - video
- `pygame` (opcjonalnie) - alternatywa dla prostych animacji

**ZarzÄ…dzanie procesem:**
- **systemd** - autostart, restart, monitoring
- **cron** - synchronizacja czasu (NTP)

**ObsĹ‚uga rotacji ekranu:**
- `xrandr` (X11) lub konfiguracja w systemie
- Automatyczna rotacja treĹ›ci w aplikacji

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
1. Konfiguracja folderu ZASTÄPSTWA w panelu admin
2. Autoryzacja OAuth 2.0 (jednorazowa)
3. Monitorowanie zmian (webhook + polling)
4. Automatyczne pobieranie nowych/zmienionych plikĂłw
5. Aktualizacja harmonogramu

### 3.5. Komunikacja

**REST API:**
- Endpointy dla CRUD operacji
- Upload/download plikĂłw
- Status wyĹ›wietlaczy

**WebSocket:**
- Status w czasie rzeczywistym
- Push aktualizacji treĹ›ci
- Synchronizacja harmonogramĂłw

**ProtokĂłĹ‚:**
- HTTPS (TLS 1.3)
- WSS (WebSocket Secure)

---

## 4. SzczegĂłĹ‚owa Struktura Bazy Danych

### 4.1. Tabele

```sql
-- UĹĽytkownicy (role: admin, operator)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'operator')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- WyĹ›wietlacze
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
    position_x INTEGER,  -- Pozycja w graficznym ukĹ‚adzie
    position_y INTEGER,
    last_seen TIMESTAMP,
    cache_size_mb INTEGER DEFAULT 1000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grupy wyĹ›wietlaczy
CREATE TABLE groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('horizontal', 'vertical', 'mixed', 'single')),
    floor VARCHAR(50),
    layout_config JSONB,  -- Konfiguracja graficznego ukĹ‚adu
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TreĹ›ci
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
    display_duration_seconds INTEGER,  -- Czas wyĹ›wietlania treĹ›ci
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Harmonogramy wĹ‚Ä…czania TV
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

-- Logi aktywnoĹ›ci (dla operatora)
CREATE TABLE activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),  -- 'content', 'display', 'schedule', etc.
    entity_id INTEGER,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Status wyĹ›wietlaczy (cache)
CREATE TABLE display_status (
    display_id INTEGER PRIMARY KEY REFERENCES displays(id) ON DELETE CASCADE,
    current_content_id INTEGER REFERENCES content(id),
    current_schedule_id INTEGER REFERENCES schedules(id),
    cache_status JSONB,  -- Status cache (co jest pobrane, co brakuje)
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Historia statusĂłw wyĹ›wietlaczy (dla raportĂłw)
CREATE TABLE display_status_history (
    id SERIAL PRIMARY KEY,
    display_id INTEGER REFERENCES displays(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('online', 'offline', 'error')),
    last_seen TIMESTAMP,
    connection_lost_at TIMESTAMP,  -- Kiedy stracono poĹ‚Ä…czenie
    connection_restored_at TIMESTAMP,  -- Kiedy przywrĂłcono poĹ‚Ä…czenie
    duration_offline_seconds INTEGER,  -- Czas offline w sekundach
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alerty (brak komunikacji, bĹ‚Ä™dy)
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

-- Harmonogramy dzwonkĂłw szkolnych
CREATE TABLE bell_schedules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,  -- np. "Dzwonek na lekcjÄ™", "Dzwonek na przerwÄ™"
    bell_time TIME NOT NULL,
    days_of_week INTEGER[],  -- [1,2,3,4,5] = pon-pt
    start_date DATE,
    end_date DATE,
    sound_file_path VARCHAR(500),  -- ĹšcieĹĽka do pliku dĹşwiÄ™kowego
    volume INTEGER DEFAULT 50 CHECK (volume >= 0 AND volume <= 100),
    play_on_displays BOOLEAN DEFAULT TRUE,  -- Czy odtwarzaÄ‡ na wyĹ›wietlaczach
    display_ids INTEGER[],  -- Lista ID wyĹ›wietlaczy (puste = wszystkie)
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Historia odtworzeĹ„ dzwonkĂłw
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

## 5. SzczegĂłĹ‚owe PrzepĹ‚ywy DziaĹ‚ania

### 5.1. Upload TreĹ›ci (Admin)

1. **Admin loguje siÄ™** â†’ JWT token
2. **Upload pliku** â†’ POST `/api/content/upload`
   - Walidacja typu pliku
   - Zapis do `/content/original/`
   - Utworzenie rekordu w `content`
   - ZwrĂłcenie `content_id`
3. **Przetwarzanie w tle** (Celery):
   - **Video**: Transkodowanie do MP4 (H.264, 1920Ă—1080)
   - **PDF**: Generowanie miniatur
   - **Excel**: Analiza struktury (liczba wierszy, kolumn)
   - **Obrazy**: Generowanie miniatur, optymalizacja
4. **Aktualizacja statusu** â†’ `processing_jobs.status = 'completed'`
5. **Gotowe do uĹĽycia** â†’ TreĹ›Ä‡ dostÄ™pna w harmonogramach

### 5.2. Konfiguracja Grup i WyĹ›wietlaczy (Admin)

1. **Graficzny edytor ukĹ‚adu**:
   - Drag & drop wyĹ›wietlaczy na wizualizacji budynku
   - Przypisanie do piÄ™ter
   - Konfiguracja grup (np. "3 monitory pionowe")
2. **Zapis konfiguracji**:
   - `groups.layout_config` (JSON) - pozycje, rozmiary
   - `displays.group_id`, `displays.floor`, `displays.position_x/y`
3. **Walidacja**:
   - Sprawdzenie czy wyĹ›wietlacz nie jest w wielu grupach
   - Sprawdzenie czy grupa ma sens (np. 3 monitory pionowe = 3 wyĹ›wietlacze)

### 5.3. Tworzenie Harmonogramu (Admin)

1. **WybĂłr treĹ›ci** â†’ Lista dostÄ™pnych treĹ›ci
2. **WybĂłr wyĹ›wietlacza/grupy**:
   - Pojedynczy wyĹ›wietlacz
   - Grupa wyĹ›wietlaczy
   - Wszystkie wyĹ›wietlacze
3. **Konfiguracja czasu**:
   - Czas wyĹ›wietlania (start_time, end_time)
   - Daty (start_date, end_date) - opcjonalnie
   - Dni tygodnia
   - Czas wyĹ›wietlania treĹ›ci (display_duration_seconds)
4. **Priorytet** â†’ JeĹ›li wiele treĹ›ci w tym samym czasie
5. **Zapis** â†’ `schedules` table
6. **Push do wyĹ›wietlaczy** â†’ WebSocket notification

### 5.4. DziaĹ‚anie WyĹ›wietlacza (Klient)

1. **Start systemu** (systemd):
   - Uruchomienie aplikacji klienta
   - PoĹ‚Ä…czenie z serwerem (REST API)
   - Rejestracja wyĹ›wietlacza (MAC address)
2. **Pobranie konfiguracji**:
   - GET `/api/displays/{id}/config`
   - Orientacja, rozdzielczoĹ›Ä‡, grupa
3. **Pobranie harmonogramu**:
   - GET `/api/displays/{id}/schedule`
   - Lista treĹ›ci z czasami
4. **Pobranie treĹ›ci** (cache):
   - Sprawdzenie co jest w cache lokalnym
   - Pobranie brakujÄ…cych plikĂłw (GET `/api/content/{id}/download`)
   - Zapis do lokalnego cache
5. **WyĹ›wietlanie**:
   - Sprawdzenie aktualnego czasu
   - WybĂłr treĹ›ci zgodnie z harmonogramem
   - WyĹ›wietlenie:
     - **Obraz**: Pillow â†’ PyQt6
     - **PDF**: pdf2image â†’ Pillow â†’ PyQt6
     - **Excel**: openpyxl â†’ renderowanie â†’ PyQt6
     - **Video**: VLC/mpv player
6. **Status w czasie rzeczywistym**:
   - WebSocket â†’ wysyĹ‚anie statusu co 30s
   - Aktualna treĹ›Ä‡, status cache, bĹ‚Ä™dy
7. **ObsĹ‚uga offline**:
   - JeĹ›li brak poĹ‚Ä…czenia â†’ wyĹ›wietlanie z cache
   - Retry poĹ‚Ä…czenia co 60s
   - Queue aktualizacji

### 5.5. Integracja Google Drive (ZASTÄPSTWA)

1. **Konfiguracja** (Admin):
   - Autoryzacja OAuth 2.0 (jednorazowa)
   - WybĂłr folderu ZASTÄPSTWA
   - Zapis `cloud_sync` record
2. **Monitorowanie zmian**:
   - **Webhook** (preferowane): Google Drive Push notifications
   - **Polling** (fallback): Sprawdzanie co 5 minut
3. **Wykrycie zmiany**:
   - Nowy plik â†’ pobranie â†’ upload do systemu
   - Zmieniony plik â†’ pobranie â†’ aktualizacja
   - UsuniÄ™ty plik â†’ usuniÄ™cie z systemu
4. **Automatyczna aktualizacja harmonogramu**:
   - JeĹ›li `auto_schedule = TRUE`:
     - Nowy plik â†’ utworzenie harmonogramu (domyĹ›lny czas)
     - Zmieniony plik â†’ aktualizacja harmonogramu
5. **Synchronizacja**:
   - Pobranie pliku z Google Drive
   - Upload do systemu (jak normalny upload)
   - Przetwarzanie (transkodowanie, etc.)
   - Aktualizacja `cloud_files` record

### 5.6. Dzielenie DĹ‚ugich PlikĂłw Excel

**Algorytm dla grup pionowych (3 monitory obok siebie):**

1. **Analiza pliku Excel**:
   - Liczba wierszy danych
   - Liczba kolumn
   - Rozmiar czcionki (domyĹ›lny)
2. **Obliczenie podziaĹ‚u**:
   - Wiersze na monitor = `total_rows / number_of_displays`
   - Dla kaĹĽdego wyĹ›wietlacza: zakres wierszy
3. **Renderowanie**:
   - Dla kaĹĽdego wyĹ›wietlacza:
     - WyciÄ…gniÄ™cie odpowiedniego zakresu wierszy
     - Renderowanie do obrazu (1920Ă—1080, obrĂłcony 90Â°)
     - Zapis jako osobna "wersja" treĹ›ci
4. **Przypisanie do harmonogramu**:
   - Ta sama treĹ›Ä‡, rĂłĹĽne "wersje" dla kaĹĽdego wyĹ›wietlacza w grupie
   - Synchronizacja czasu wyĹ›wietlania

**Implementacja:**
- `content.metadata` â†’ `{"split_config": {"group_id": 1, "display_index": 0, "row_range": [0, 50]}}`
- Klient pobiera odpowiedniÄ… wersjÄ™ dla swojego wyĹ›wietlacza

### 5.7. Symulacja WyĹ›wietlania (Publiczna Strona)

1. **DostÄ™p bez logowania**:
   - GET `/simulation` (publiczny endpoint)
   - WyĹ›wietlenie wizualizacji wszystkich wyĹ›wietlaczy
2. **Wizualizacja**:
   - Graficzny ukĹ‚ad monitorĂłw (zgodnie z konfiguracjÄ…)
   - PodglÄ…d aktualnie wyĹ›wietlanej treĹ›ci na kaĹĽdym monitorze
   - Status (online/offline)
3. **Aktualizacja w czasie rzeczywistym**:
   - WebSocket (publiczny, read-only)
   - Aktualizacja co 5-10 sekund
4. **Funkcje**:
   - Przewijanie miÄ™dzy piÄ™trami
   - Zoom na konkretny monitor
   - PodglÄ…d harmonogramu

---

## 6. ObsĹ‚uga FormatĂłw - SzczegĂłĹ‚y

### 6.1. PDF

**Przetwarzanie:**
- `pdf2image` â†’ konwersja kaĹĽdej strony do PNG
- Skalowanie do 1920Ă—1080 (z zachowaniem proporcji)
- JeĹ›li wiele stron â†’ wybĂłr pierwszej strony lub przewijanie

**WyĹ›wietlanie:**
- Klient: PNG â†’ Pillow â†’ PyQt6
- PeĹ‚noekranowy tryb

### 6.2. Excel

**Przetwarzanie:**
- `openpyxl` â†’ odczyt danych
- Analiza struktury (liczba wierszy, kolumn)
- Dla dĹ‚ugich plikĂłw â†’ przygotowanie podziaĹ‚u

**Renderowanie:**
- `pandas` + `matplotlib` lub wĹ‚asny renderer
- Skalowanie do 1920Ă—1080
- Automatyczne dopasowanie czcionki
- Dla grup pionowych â†’ podziaĹ‚ wierszy

**WyĹ›wietlanie:**
- Obraz PNG â†’ Pillow â†’ PyQt6

### 6.3. Obrazy (JPG, PNG, GIF)

**Przetwarzanie:**
- `Pillow` â†’ optymalizacja, skalowanie
- Dla GIF â†’ konwersja do animacji lub pierwsza klatka

**WyĹ›wietlanie:**
- Pillow â†’ PyQt6
- PeĹ‚noekranowy tryb

### 6.4. Video (MPG â†’ MP4)

**Transkodowanie na serwerze (FFmpeg):**
```bash
ffmpeg -i input.mpg -c:v libx264 -preset medium -crf 23 \
  -c:a aac -b:a 128k -s 1920x1080 -r 30 output.mp4
```

**Parametry:**
- Codec: H.264 (libx264)
- RozdzielczoĹ›Ä‡: 1920Ă—1080 (FHD)
- Frame rate: 30 fps
- Audio: AAC 128kbps
- CRF: 23 (dobra jakoĹ›Ä‡, rozsÄ…dny rozmiar)

**WyĹ›wietlanie:**
- VLC Python bindings lub mpv
- PeĹ‚noekranowy tryb
- Loop (jeĹ›li potrzeba)

---

## 7. ObsĹ‚uga Rotacji Ekranu (90Â°)

### 7.1. Poziom Systemu

**Konfiguracja X11 (jeĹ›li X11):**
```bash
xrandr --output HDMI-1 --rotate left  # 90Â° w lewo
```

**Konfiguracja w aplikacji:**
- `displays.orientation = 90`
- Automatyczna rotacja treĹ›ci w PyQt6

### 7.2. Poziom Aplikacji

**PyQt6:**
```python
# Rotacja treĹ›ci
transform = QTransform().rotate(90)
pixmap = pixmap.transformed(transform)
```

**Dla grup pionowych:**
- 3 monitory obok siebie, kaĹĽdy obrĂłcony 90Â°
- TreĹ›Ä‡ renderowana z uwzglÄ™dnieniem rotacji
- Dzielenie Excel z uwzglÄ™dnieniem rotacji

---

## 8. System Autoryzacji i RĂłl

### 8.1. Role

**Admin:**
- Wszystkie operacje CRUD
- Upload treĹ›ci
- Konfiguracja wyĹ›wietlaczy i grup
- Tworzenie harmonogramĂłw
- Konfiguracja Google Drive
- ZarzÄ…dzanie uĹĽytkownikami

**Operator:**
- Tylko odczyt (GET)
- PodglÄ…d statusu wyĹ›wietlaczy
- PodglÄ…d harmonogramĂłw
- PodglÄ…d treĹ›ci
- Logi aktywnoĹ›ci

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

## 9. ObsĹ‚uga BĹ‚Ä™dĂłw i NiezawodnoĹ›Ä‡

### 9.1. WiFi - OpĂłĹşnienia i Zrywane PoĹ‚Ä…czenia

**Strategia:**
1. **Lokalny cache**:
   - Wszystkie treĹ›ci w cache lokalnym
   - Minimalna zaleĹĽnoĹ›Ä‡ od sieci podczas wyĹ›wietlania
2. **Pobieranie w tle**:
   - Pobieranie nowych treĹ›ci przed czasem wyĹ›wietlania
   - Retry z exponential backoff
3. **Status offline**:
   - WyĹ›wietlanie z cache
   - Queue aktualizacji
   - Automatyczne synchronizowanie po powrocie poĹ‚Ä…czenia
4. **Weryfikacja integralnoĹ›ci**:
   - Checksum (MD5/SHA256) dla kaĹĽdego pliku
   - Weryfikacja przy pobieraniu

### 9.2. Przetwarzanie Video - BĹ‚Ä™dy

**ObsĹ‚uga:**
- Retry (3 prĂłby)
- Logowanie bĹ‚Ä™dĂłw
- Powiadomienie admina (email/panel)
- Fallback: wyĹ›wietlanie oryginalnego pliku (jeĹ›li moĹĽliwe)

### 9.3. Synchronizacja Google Drive - BĹ‚Ä™dy

**ObsĹ‚uga:**
- Retry z exponential backoff
- Logowanie bĹ‚Ä™dĂłw
- Powiadomienie admina
- Fallback: polling zamiast webhook

---

## 10. BezpieczeĹ„stwo

### 10.1. Serwer

- HTTPS (Let's Encrypt)
- Firewall (UFW)
- Regularne aktualizacje
- Backup bazy danych (codziennie)
- Backup plikĂłw (tygodniowo)

### 10.2. Autentykacja

- Silne hasĹ‚a (min. 12 znakĂłw)
- JWT tokens
- Rate limiting
- CORS configuration

### 10.3. WyĹ›wietlacze

- Autoryzacja przez MAC address
- HTTPS komunikacja
- Read-only dostÄ™p do API (tylko GET dla swoich danych)

---

## 10A. System Monitorowania Statusu WyĹ›wietlaczy

### 10A.1. Mechanizm Wykrywania Braku Komunikacji

**Heartbeat System:**
- WyĹ›wietlacz wysyĹ‚a status co 30 sekund (WebSocket lub REST API)
- Serwer oczekuje heartbeat w oknie 60 sekund
- JeĹ›li brak heartbeat przez 60s â†’ status = 'offline'
- JeĹ›li brak heartbeat przez 5 minut â†’ alert 'connection_lost'

**Endpointy:**
- POST `/api/displays/{id}/heartbeat` - wyĹ›wietlacz wysyĹ‚a status
- GET `/api/displays/{id}/status` - aktualny status
- GET `/api/displays/status/all` - status wszystkich wyĹ›wietlaczy

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
- Lista wszystkich wyĹ›wietlaczy z aktualnym statusem
- Wizualizacja:
  - đźź˘ Online (zielony)
  - đź”´ Offline (czerwony)
  - đźźˇ Error (ĹĽĂłĹ‚ty)
- Czas ostatniego poĹ‚Ä…czenia
- Czas offline (jeĹ›li offline)
- Aktualizacja w czasie rzeczywistym (WebSocket)

**Filtry:**
- Status (online/offline/error)
- PiÄ™tro
- Grupa

**SzczegĂłĹ‚y wyĹ›wietlacza:**
- Historia statusĂłw (ostatnie 24h)
- Aktualna treĹ›Ä‡
- Status cache
- BĹ‚Ä™dy

### 10A.3. System AlertĂłw

**Typy alertĂłw:**
1. **connection_lost** - Brak komunikacji > 5 minut
2. **connection_restored** - PrzywrĂłcono komunikacjÄ™
3. **error** - BĹ‚Ä…d w dziaĹ‚aniu wyĹ›wietlacza
4. **cache_missing** - Brakuje plikĂłw w cache

**Severity:**
- **critical**: Brak komunikacji > 30 minut
- **error**: Brak komunikacji 5-30 minut, bĹ‚Ä™dy
- **warning**: Brak komunikacji < 5 minut
- **info**: PrzywrĂłcono komunikacjÄ™

**WyĹ›wietlanie alertĂłw:**
- Lista aktywnych alertĂłw na stronie statusu
- Licznik nieprzeczytanych alertĂłw
- Oznaczanie jako przeczytane/rozwiÄ…zane

### 10A.4. Raportowanie

**Raporty dostÄ™pne dla Admin i Operator:**
1. **Raport dzienny** - Status wyĹ›wietlaczy w ciÄ…gu dnia
2. **Raport tygodniowy** - Statystyki dostÄ™pnoĹ›ci
3. **Raport offline** - Czas offline dla kaĹĽdego wyĹ›wietlacza

**Endpointy:**
- GET `/api/reports/daily?date=2024-01-15`
- GET `/api/reports/weekly?week=2024-W03`
- GET `/api/reports/offline?display_id=1&start_date=...&end_date=...`

**Dane w raporcie:**
- Czas online/offline
- Liczba przerw w komunikacji
- Ĺšredni czas offline
- NajdĹ‚uĹĽszy okres offline
- Wykresy dostÄ™pnoĹ›ci

**Eksport:**
- PDF (dla operatora)
- CSV (dla admina)

---

## 10B. System "Przyjaznych DzwonkĂłw" Szkolnych

### 10B.1. Koncepcja

System odtwarzania dzwonkĂłw szkolnych zgodnie z harmonogramem:
- Dzwonek na lekcjÄ™
- Dzwonek na przerwÄ™
- Dzwonek na obiad
- Dzwonek na koniec zajÄ™Ä‡

**Funkcje:**
- Harmonogramy dla rĂłĹĽnych dni tygodnia
- RĂłĹĽne dĹşwiÄ™ki dla rĂłĹĽnych typĂłw dzwonkĂłw
- Odtwarzanie na wyĹ›wietlaczach (gĹ‚oĹ›niki wbudowane lub zewnÄ™trzne)
- MoĹĽliwoĹ›Ä‡ wyĹ‚Ä…czenia na wybranych wyĹ›wietlaczach

### 10B.2. ZarzÄ…dzanie Dzwonkami (Admin)

**Panel konfiguracji:**
1. **Lista harmonogramĂłw dzwonkĂłw**
   - Nazwa (np. "Dzwonek na lekcjÄ™ - 1")
   - Czas (np. 08:00)
   - Dni tygodnia
   - Plik dĹşwiÄ™kowy
   - GĹ‚oĹ›noĹ›Ä‡
   - WyĹ›wietlacze (wszystkie lub wybrane)

2. **Upload plikĂłw dĹşwiÄ™kowych**
   - Format: MP3, WAV, OGG
   - Walidacja dĹ‚ugoĹ›ci (max 30 sekund)
   - PodglÄ…d odtwarzania

3. **Harmonogram tygodniowy**
   - Widok kalendarza z dzwonkami
   - MoĹĽliwoĹ›Ä‡ kopiowania miÄ™dzy dniami
   - Import/export harmonogramu

### 10B.3. Odtwarzanie DzwonkĂłw

**Mechanizm:**
1. **Serwer:**
   - Cron job lub scheduler (Celery Beat)
   - Sprawdzenie harmonogramu co minutÄ™
   - JeĹ›li czas dzwonka â†’ wysĹ‚anie komendy do wyĹ›wietlaczy

2. **WyĹ›wietlacze:**
   - Odbieranie komendy przez WebSocket lub REST API
   - Pobranie pliku dĹşwiÄ™kowego (jeĹ›li nie ma w cache)
   - Odtworzenie dĹşwiÄ™ku (pygame, vlc-python, lub systemowy player)
   - Logowanie odtworzenia

**ObsĹ‚uga:**
- JeĹ›li wyĹ›wietlacz offline â†’ pominiÄ™cie (logowanie)
- JeĹ›li brak pliku â†’ prĂłba pobrania, fallback do domyĹ›lnego dĹşwiÄ™ku
- JeĹ›li wyĹ›wietlacz wyciszony â†’ pominiÄ™cie

### 10B.4. Integracja z WyĹ›wietlaczami

**Opcje odtwarzania:**
1. **Na wyĹ›wietlaczu** (HP T630):
   - GĹ‚oĹ›niki wbudowane (jeĹ›li dostÄ™pne)
   - GĹ‚oĹ›niki USB
   - WyjĹ›cie audio (3.5mm)

2. **Przez system audio szkoĹ‚y** (opcjonalnie):
   - Integracja z systemem nagĹ‚oĹ›nienia
   - API do sterowania

### 10B.5. Historia i Logi

**Tabela `bell_history`:**
- Kiedy odtworzono dzwonek
- Status (sukces/bĹ‚Ä…d)
- KtĂłre wyĹ›wietlacze odtworzyĹ‚y
- BĹ‚Ä™dy (jeĹ›li wystÄ…piĹ‚y)

**Raporty:**
- Statystyki odtworzeĹ„
- WyĹ›wietlacze, ktĂłre nie odtworzyĹ‚y
- CzÄ™stotliwoĹ›Ä‡ bĹ‚Ä™dĂłw

---

## 10C. Ĺšrodowisko Hyper-V

### 10C.1. Konfiguracja Maszyny Wirtualnej

**Specyfikacje zalecane:**
- **CPU**: 4 vCPU (minimum 2)
- **RAM**: 8 GB (minimum 4 GB)
- **Dysk**: 100 GB (SSD preferowane)
- **SieÄ‡**: Bridge mode (dostÄ™p z sieci lokalnej)

**System operacyjny:**
- Ubuntu Server 22.04 LTS
- Aktualizacje automatyczne (security)

### 10C.2. Konfiguracja Sieci

**Network Adapter:**
- External Virtual Switch (dostÄ™p do sieci WiFi)
- Statyczny IP lub DHCP z rezerwacjÄ…
- Port forwarding (jeĹ›li potrzebny dostÄ™p z zewnÄ…trz)

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
   - Backup do innej lokalizacji (sieÄ‡ lokalna)

2. **Pliki treĹ›ci:**
   - `rsync` tygodniowo
   - Backup do innej lokalizacji

3. **Snapshot Hyper-V:**
   - Przed wiÄ™kszymi aktualizacjami
   - Automatyczne snapshoty (opcjonalnie)

**Odzyskiwanie:**
- Procedura przywracania z backupu
- Testowanie backupĂłw (co miesiÄ…c)

### 10C.4. Monitoring Maszyny Wirtualnej

**Metryki:**
- CPU usage
- RAM usage
- Disk usage
- Network traffic
- Uptime

**Alerty:**
- Wysokie uĹĽycie zasobĂłw (> 80%)
- Brak miejsca na dysku (< 10%)
- Brak odpowiedzi serwera

---

## 11. Plan Implementacji - SzczegĂłĹ‚owy Etapowy

### Etap 0: Przygotowanie Ĺšrodowiska (1 tydzieĹ„)

**Cel:** Przygotowanie infrastruktury i Ĺ›rodowiska deweloperskiego

**Zadania:**
1. âś… Utworzenie maszyny wirtualnej Hyper-V (Ubuntu 22.04)
2. âś… Konfiguracja sieci (bridge, statyczny IP)
3. âś… Instalacja podstawowych narzÄ™dzi (git, curl, wget)
4. âś… Instalacja PostgreSQL 14+
5. âś… Instalacja Redis
6. âś… Instalacja Python 3.10+ i pip
7. âś… Instalacja Node.js 18+ (dla frontendu)
8. âś… Konfiguracja firewall (UFW)
9. âś… Konfiguracja SSH
10. âś… Utworzenie uĹĽytkownika aplikacji

**Weryfikacja:**
- [ ] VM uruchomiona i dostÄ™pna przez SSH
- [ ] PostgreSQL dziaĹ‚a (psql --version)
- [ ] Redis dziaĹ‚a (redis-cli ping)
- [ ] Python dziaĹ‚a (python3 --version)
- [ ] Node.js dziaĹ‚a (node --version)
- [ ] Firewall skonfigurowany

**Deliverable:** DziaĹ‚ajÄ…ce Ĺ›rodowisko deweloperskie

---

### Etap 1: Backend API - Podstawy (1 tydzieĹ„)

**Cel:** Utworzenie podstawowej struktury backendu z autentykacjÄ…

**Zadania:**
1. âś… Utworzenie projektu FastAPI
2. âś… Konfiguracja struktury katalogĂłw
3. âś… PoĹ‚Ä…czenie z PostgreSQL
4. âś… PoĹ‚Ä…czenie z Redis
5. âś… Utworzenie modeli bazy danych (SQLAlchemy)
6. âś… Migracje bazy danych (Alembic)
7. âś… System autentykacji (JWT)
8. âś… Endpointy logowania/logout
9. âś… Middleware dla autoryzacji (role: admin/operator)
10. âś… Podstawowe endpointy uĹĽytkownikĂłw (CRUD)

**Weryfikacja:**
- [ ] API uruchamia siÄ™ (uvicorn)
- [ ] PoĹ‚Ä…czenie z bazÄ… dziaĹ‚a
- [ ] MoĹĽna siÄ™ zalogowaÄ‡ jako admin
- [ ] MoĹĽna siÄ™ zalogowaÄ‡ jako operator
- [ ] Role dziaĹ‚ajÄ… poprawnie (admin ma wiÄ™cej uprawnieĹ„)
- [ ] Swagger UI dostÄ™pny (/docs)

**Deliverable:** DziaĹ‚ajÄ…ce API z autentykacjÄ…

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

### Etap 2: Backend - ZarzÄ…dzanie WyĹ›wietlaczami (3 dni)

**Cel:** CRUD dla wyĹ›wietlaczy i podstawowy status

**Zadania:**
1. âś… Model Display w bazie danych
2. âś… Endpointy CRUD dla wyĹ›wietlaczy (tylko admin)
3. âś… Endpoint rejestracji wyĹ›wietlacza (przez MAC address)
4. âś… Endpoint heartbeat (POST /api/displays/{id}/heartbeat)
5. âś… Endpoint statusu (GET /api/displays/{id}/status)
6. âś… Automatyczne wykrywanie offline (brak heartbeat > 60s)
7. âś… Tabela display_status_history
8. âś… Logika aktualizacji statusu

**Weryfikacja:**
- [ ] MoĹĽna utworzyÄ‡ wyĹ›wietlacz (admin)
- [ ] MoĹĽna zobaczyÄ‡ listÄ™ wyĹ›wietlaczy (admin/operator)
- [ ] WyĹ›wietlacz moĹĽe siÄ™ zarejestrowaÄ‡ (MAC address)
- [ ] WyĹ›wietlacz moĹĽe wysyĹ‚aÄ‡ heartbeat
- [ ] Status zmienia siÄ™ na offline po braku heartbeat
- [ ] Historia statusĂłw jest zapisywana

**Deliverable:** System zarzÄ…dzania wyĹ›wietlaczami z podstawowym monitoringiem

---

### Etap 3: Backend - Upload i Przetwarzanie TreĹ›ci (1 tydzieĹ„)

**Cel:** Upload plikĂłw i podstawowe przetwarzanie

**Zadania:**
1. âś… Endpoint upload plikĂłw (POST /api/content/upload)
2. âś… Walidacja typĂłw plikĂłw (PDF, Excel, obrazy, video)
3. âś… Zapis plikĂłw do /content/original/
4. âś… Model Content w bazie danych
5. âś… Konfiguracja Celery
6. âś… Worker do przetwarzania obrazĂłw (Pillow)
7. âś… Worker do przetwarzania PDF (pdf2image)
8. âś… Worker do przetwarzania Excel (openpyxl)
9. âś… Generowanie miniatur
10. âś… Tabela processing_jobs

**Weryfikacja:**
- [ ] MoĹĽna wgraÄ‡ obraz (JPG, PNG)
- [ ] MoĹĽna wgraÄ‡ PDF
- [ ] MoĹĽna wgraÄ‡ Excel
- [ ] MoĹĽna wgraÄ‡ video (MPG)
- [ ] Pliki sÄ… zapisywane w odpowiednich folderach
- [ ] Miniatury sÄ… generowane
- [ ] Status przetwarzania jest widoczny

**Deliverable:** System uploadu i przetwarzania treĹ›ci

---

### Etap 4: Backend - Transkodowanie Video (3 dni)

**Cel:** Transkodowanie video do MP4 (H.264)

**Zadania:**
1. âś… Instalacja FFmpeg
2. âś… Worker do transkodowania video
3. âś… Konfiguracja parametrĂłw (1920Ă—1080, H.264)
4. âś… Progress tracking (0-100%)
5. âś… ObsĹ‚uga bĹ‚Ä™dĂłw transkodowania
6. âś… Zapis przetworzonego video do /content/processed/

**Weryfikacja:**
- [ ] Video MPG jest transkodowane do MP4
- [ ] RozdzielczoĹ›Ä‡ to 1920Ă—1080
- [ ] Codec to H.264
- [ ] Progress jest widoczny w API
- [ ] BĹ‚Ä™dy sÄ… logowane

**Deliverable:** System transkodowania video

---

### Etap 5: Backend - Harmonogramy TreĹ›ci (1 tydzieĹ„)

**Cel:** System harmonogramĂłw wyĹ›wietlania treĹ›ci

**Zadania:**
1. âś… Model Schedule w bazie danych
2. âś… Endpointy CRUD dla harmonogramĂłw (admin)
3. âś… Endpoint pobierania harmonogramu dla wyĹ›wietlacza
4. âś… Logika wyboru treĹ›ci na podstawie czasu
5. âś… ObsĹ‚uga dni tygodnia
6. âś… ObsĹ‚uga dat (start_date, end_date)
7. âś… Priorytety harmonogramĂłw
8. âś… Endpoint GET /api/displays/{id}/schedule

**Weryfikacja:**
- [ ] MoĹĽna utworzyÄ‡ harmonogram (admin)
- [ ] Harmonogram ma czas start/end
- [ ] Harmonogram ma dni tygodnia
- [ ] WyĹ›wietlacz moĹĽe pobraÄ‡ swĂłj harmonogram
- [ ] WybĂłr treĹ›ci dziaĹ‚a poprawnie (na podstawie czasu)
- [ ] Priorytety dziaĹ‚ajÄ…

**Deliverable:** System harmonogramĂłw treĹ›ci

---

### Etap 6: Backend - Grupowanie WyĹ›wietlaczy (3 dni)

**Cel:** System grup wyĹ›wietlaczy

**Zadania:**
1. âś… Model Group w bazie danych
2. âś… Endpointy CRUD dla grup (admin)
3. âś… Przypisywanie wyĹ›wietlaczy do grup
4. âś… Typy grup (horizontal, vertical, mixed, single)
5. âś… Harmonogramy dla grup (zamiast pojedynczych wyĹ›wietlaczy)
6. âś… Endpoint GET /api/groups/{id}/displays

**Weryfikacja:**
- [ ] MoĹĽna utworzyÄ‡ grupÄ™ (admin)
- [ ] MoĹĽna przypisaÄ‡ wyĹ›wietlacz do grupy
- [ ] Harmonogram moĹĽe byÄ‡ przypisany do grupy
- [ ] Wszystkie wyĹ›wietlacze w grupie otrzymujÄ… ten sam harmonogram

**Deliverable:** System grupowania wyĹ›wietlaczy

---

### Etap 7: Backend - Monitoring i Alerty (1 tydzieĹ„)

**Cel:** System monitorowania statusu i alertĂłw

**Zadania:**
1. âś… Tabela alerts w bazie danych
2. âś… Automatyczne tworzenie alertĂłw (connection_lost)
3. âś… Automatyczne rozwiÄ…zywanie alertĂłw (connection_restored)
4. âś… Endpoint GET /api/alerts (lista alertĂłw)
5. âś… Endpoint PUT /api/alerts/{id}/resolve (oznaczenie jako rozwiÄ…zane)
6. âś… Endpoint GET /api/displays/status/all (status wszystkich)
7. âś… Tabela display_status_history
8. âś… Endpoint GET /api/displays/{id}/status-history

**Weryfikacja:**
- [ ] Alert jest tworzony gdy wyĹ›wietlacz traci poĹ‚Ä…czenie > 5 min
- [ ] Alert jest automatycznie rozwiÄ…zany gdy poĹ‚Ä…czenie wraca
- [ ] MoĹĽna zobaczyÄ‡ listÄ™ aktywnych alertĂłw
- [ ] MoĹĽna oznaczyÄ‡ alert jako rozwiÄ…zany
- [ ] Historia statusĂłw jest zapisywana
- [ ] MoĹĽna zobaczyÄ‡ historiÄ™ statusĂłw wyĹ›wietlacza

**Deliverable:** System monitorowania i alertĂłw

---

### Etap 8: Backend - Raportowanie (3 dni)

**Cel:** System raportĂłw statusu wyĹ›wietlaczy

**Zadania:**
1. âś… Endpoint GET /api/reports/daily (raport dzienny)
2. âś… Endpoint GET /api/reports/weekly (raport tygodniowy)
3. âś… Endpoint GET /api/reports/offline (raport offline)
4. âś… Obliczanie statystyk (czas online/offline)
5. âś… Eksport do CSV (dla admina)
6. âś… Eksport do PDF (dla operatora) - opcjonalnie

**Weryfikacja:**
- [ ] Raport dzienny pokazuje statystyki dla dnia
- [ ] Raport tygodniowy pokazuje statystyki dla tygodnia
- [ ] Raport offline pokazuje czas offline dla wyĹ›wietlacza
- [ ] Eksport CSV dziaĹ‚a
- [ ] Dane w raportach sÄ… poprawne

**Deliverable:** System raportowania

---

### Etap 9: Backend - System DzwonkĂłw (1 tydzieĹ„)

**Cel:** System harmonogramĂłw i odtwarzania dzwonkĂłw szkolnych

**Zadania:**
1. âś… Tabela bell_schedules w bazie danych
2. âś… Endpointy CRUD dla harmonogramĂłw dzwonkĂłw (admin)
3. âś… Upload plikĂłw dĹşwiÄ™kowych
4. âś… Konfiguracja Celery Beat (scheduler)
5. âś… Task do sprawdzania harmonogramu dzwonkĂłw (co minutÄ™)
6. âś… Endpoint POST /api/displays/{id}/play-bell (odtwarzanie dzwonka)
7. âś… Tabela bell_history
8. âś… Logowanie odtworzeĹ„ dzwonkĂłw

**Weryfikacja:**
- [ ] MoĹĽna utworzyÄ‡ harmonogram dzwonka (admin)
- [ ] MoĹĽna wgraÄ‡ plik dĹşwiÄ™kowy
- [ ] Scheduler sprawdza harmonogram co minutÄ™
- [ ] Komenda odtwarzania jest wysyĹ‚ana do wyĹ›wietlaczy
- [ ] Historia odtworzeĹ„ jest zapisywana

**Deliverable:** System dzwonkĂłw szkolnych (backend)

---

### Etap 10: Frontend - Podstawowa Struktura (1 tydzieĹ„)

**Cel:** Utworzenie podstawowej struktury frontendu

**Zadania:**
1. âś… Utworzenie projektu React + TypeScript
2. âś… Konfiguracja routing (React Router)
3. âś… Konfiguracja Axios (HTTP client)
4. âś… Konfiguracja WebSocket (Socket.io-client)
5. âś… Strona logowania
6. âś… Layout gĹ‚Ăłwny (sidebar, header)
7. âś… Dashboard (podstawowy)
8. âś… Integracja z backendem (logowanie)

**Weryfikacja:**
- [ ] Aplikacja siÄ™ uruchamia (npm start)
- [ ] MoĹĽna siÄ™ zalogowaÄ‡
- [ ] Routing dziaĹ‚a
- [ ] PoĹ‚Ä…czenie z API dziaĹ‚a
- [ ] Layout jest responsywny

**Deliverable:** DziaĹ‚ajÄ…cy frontend z logowaniem

---

### Etap 11: Frontend - ZarzÄ…dzanie WyĹ›wietlaczami (1 tydzieĹ„)

**Cel:** Panel do zarzÄ…dzania wyĹ›wietlaczami

**Zadania:**
1. âś… Lista wyĹ›wietlaczy (tabela)
2. âś… Formularz dodawania/edycji wyĹ›wietlacza (admin)
3. âś… Usuwanie wyĹ›wietlacza (admin)
4. âś… SzczegĂłĹ‚y wyĹ›wietlacza
5. âś… Status wyĹ›wietlacza (online/offline) z kolorem
6. âś… Historia statusĂłw (wykres)
7. âś… Filtry (status, piÄ™tro, grupa)

**Weryfikacja:**
- [ ] Lista wyĹ›wietlaczy siÄ™ wyĹ›wietla
- [ ] MoĹĽna dodaÄ‡ wyĹ›wietlacz (admin)
- [ ] MoĹĽna edytowaÄ‡ wyĹ›wietlacz (admin)
- [ ] MoĹĽna usunÄ…Ä‡ wyĹ›wietlacz (admin)
- [ ] Status jest widoczny z kolorem
- [ ] Historia statusĂłw jest widoczna

**Deliverable:** Panel zarzÄ…dzania wyĹ›wietlaczami

---

### Etap 12: Frontend - Strona Statusu (1 tydzieĹ„)

**Cel:** Strona statusu z monitoringiem w czasie rzeczywistym

**Zadania:**
1. âś… Strona statusu wszystkich wyĹ›wietlaczy
2. âś… Wizualizacja statusu (kolorowe ikony)
3. âś… WebSocket dla aktualizacji w czasie rzeczywistym
4. âś… Lista aktywnych alertĂłw
5. âś… SzczegĂłĹ‚y wyĹ›wietlacza (modal)
6. âś… Filtry i sortowanie
7. âś… OdĹ›wieĹĽanie automatyczne

**Weryfikacja:**
- [ ] Strona statusu wyĹ›wietla wszystkie wyĹ›wietlacze
- [ ] Status jest aktualizowany w czasie rzeczywistym
- [ ] Alerty sÄ… widoczne
- [ ] MoĹĽna zobaczyÄ‡ szczegĂłĹ‚y wyĹ›wietlacza
- [ ] Filtry dziaĹ‚ajÄ…

**Deliverable:** Strona statusu z monitoringiem

---

### Etap 13: Frontend - Upload TreĹ›ci (1 tydzieĹ„)

**Cel:** Panel do uploadu i zarzÄ…dzania treĹ›ciÄ…

**Zadania:**
1. âś… Lista treĹ›ci (tabela z miniaturami)
2. âś… Formularz upload (drag & drop)
3. âś… Progress bar podczas uploadu
4. âś… Status przetwarzania (pending/processing/completed)
5. âś… PodglÄ…d treĹ›ci (obrazy, PDF, video)
6. âś… Usuwanie treĹ›ci (admin)
7. âś… Filtry (typ, status)

**Weryfikacja:**
- [ ] MoĹĽna wgraÄ‡ plik (drag & drop)
- [ ] Progress bar dziaĹ‚a
- [ ] Status przetwarzania jest widoczny
- [ ] MoĹĽna zobaczyÄ‡ podglÄ…d treĹ›ci
- [ ] MoĹĽna usunÄ…Ä‡ treĹ›Ä‡ (admin)

**Deliverable:** Panel uploadu i zarzÄ…dzania treĹ›ciÄ…

---

### Etap 14: Frontend - Harmonogramy (1 tydzieĹ„)

**Cel:** Panel do zarzÄ…dzania harmonogramami

**Zadania:**
1. âś… Lista harmonogramĂłw
2. âś… Formularz tworzenia/edycji harmonogramu
3. âś… WybĂłr treĹ›ci (dropdown)
4. âś… WybĂłr wyĹ›wietlacza/grupy
5. âś… Konfiguracja czasu (start/end)
6. âś… Konfiguracja dni tygodnia
7. âś… Konfiguracja dat (start/end)
8. âś… Priorytety
9. âś… Kalendarz harmonogramĂłw

**Weryfikacja:**
- [ ] MoĹĽna utworzyÄ‡ harmonogram (admin)
- [ ] MoĹĽna edytowaÄ‡ harmonogram (admin)
- [ ] MoĹĽna usunÄ…Ä‡ harmonogram (admin)
- [ ] Kalendarz pokazuje harmonogramy
- [ ] Wszystkie opcje konfiguracji dziaĹ‚ajÄ…

**Deliverable:** Panel zarzÄ…dzania harmonogramami

---

### Etap 15: Frontend - Raporty (3 dni)

**Cel:** Panel raportĂłw

**Zadania:**
1. âś… Strona raportĂłw
2. âś… Formularz wyboru zakresu dat
3. âś… Raport dzienny (tabela + wykres)
4. âś… Raport tygodniowy (tabela + wykres)
5. âś… Raport offline (tabela)
6. âś… Eksport do CSV
7. âś… Eksport do PDF (opcjonalnie)

**Weryfikacja:**
- [ ] Raporty siÄ™ generujÄ…
- [ ] Wykresy sÄ… czytelne
- [ ] Eksport CSV dziaĹ‚a
- [ ] Dane w raportach sÄ… poprawne

**Deliverable:** Panel raportĂłw

---

### Etap 16: Frontend - System DzwonkĂłw (1 tydzieĹ„)

**Cel:** Panel zarzÄ…dzania dzwonkami szkolnymi

**Zadania:**
1. âś… Lista harmonogramĂłw dzwonkĂłw
2. âś… Formularz tworzenia/edycji harmonogramu dzwonka
3. âś… Upload plikĂłw dĹşwiÄ™kowych
4. âś… PodglÄ…d odtwarzania dĹşwiÄ™ku
5. âś… Konfiguracja gĹ‚oĹ›noĹ›ci
6. âś… WybĂłr wyĹ›wietlaczy
7. âś… Kalendarz dzwonkĂłw
8. âś… Historia odtworzeĹ„

**Weryfikacja:**
- [ ] MoĹĽna utworzyÄ‡ harmonogram dzwonka (admin)
- [ ] MoĹĽna wgraÄ‡ plik dĹşwiÄ™kowy
- [ ] MoĹĽna odsĹ‚uchaÄ‡ dĹşwiÄ™k
- [ ] Kalendarz pokazuje dzwonki
- [ ] Historia odtworzeĹ„ jest widoczna

**Deliverable:** Panel zarzÄ…dzania dzwonkami

---

### Etap 17: Klient - Podstawowa Aplikacja (1 tydzieĹ„)

**Cel:** Podstawowa aplikacja klienta na wyĹ›wietlaczu

**Zadania:**
1. âś… Utworzenie aplikacji Python + PyQt6
2. âś… PeĹ‚noekranowy tryb
3. âś… PoĹ‚Ä…czenie z API (REST)
4. âś… Rejestracja wyĹ›wietlacza (MAC address)
5. âś… Pobieranie konfiguracji
6. âś… Pobieranie harmonogramu
7. âś… Podstawowe wyĹ›wietlanie obrazu
8. âś… Systemd service (autostart)

**Weryfikacja:**
- [ ] Aplikacja uruchamia siÄ™
- [ ] Aplikacja Ĺ‚Ä…czy siÄ™ z serwerem
- [ ] WyĹ›wietlacz rejestruje siÄ™
- [ ] Aplikacja pobiera harmonogram
- [ ] Obraz jest wyĹ›wietlany peĹ‚noekranowo
- [ ] Aplikacja startuje automatycznie (systemd)

**Deliverable:** Podstawowa aplikacja klienta

---

### Etap 18: Klient - WyĹ›wietlanie FormatĂłw (1 tydzieĹ„)

**Cel:** ObsĹ‚uga wszystkich formatĂłw treĹ›ci

**Zadania:**
1. âś… WyĹ›wietlanie obrazĂłw (JPG, PNG)
2. âś… WyĹ›wietlanie PDF (pdf2image)
3. âś… WyĹ›wietlanie Excel (openpyxl + renderowanie)
4. âś… WyĹ›wietlanie video (VLC/mpv)
5. âś… Skalowanie do 1920Ă—1080
6. âś… ObsĹ‚uga rotacji 90Â°
7. âś… PrzeĹ‚Ä…czanie treĹ›ci zgodnie z harmonogramem

**Weryfikacja:**
- [ ] Obrazy sÄ… wyĹ›wietlane poprawnie
- [ ] PDF jest wyĹ›wietlany (pierwsza strona)
- [ ] Excel jest wyĹ›wietlany (renderowany)
- [ ] Video jest odtwarzane
- [ ] Rotacja 90Â° dziaĹ‚a
- [ ] PrzeĹ‚Ä…czanie treĹ›ci dziaĹ‚a zgodnie z harmonogramem

**Deliverable:** Klient z peĹ‚nÄ… obsĹ‚ugÄ… formatĂłw

---

### Etap 19: Klient - Cache i Offline (1 tydzieĹ„)

**Cel:** System cache i obsĹ‚uga offline

**Zadania:**
1. âś… Lokalny cache plikĂłw (/cache/)
2. âś… Pobieranie treĹ›ci w tle
3. âś… Weryfikacja checksum (integralnoĹ›Ä‡)
4. âś… ObsĹ‚uga offline (wyĹ›wietlanie z cache)
5. âś… Retry poĹ‚Ä…czenia (exponential backoff)
6. âś… Queue aktualizacji
7. âś… Status cache (co jest, czego brakuje)
8. âś… Heartbeat (co 30s)

**Weryfikacja:**
- [ ] Pliki sÄ… cache'owane lokalnie
- [ ] Pobieranie w tle dziaĹ‚a
- [ ] WyĹ›wietlanie z cache dziaĹ‚a (offline)
- [ ] Retry dziaĹ‚a po powrocie poĹ‚Ä…czenia
- [ ] Heartbeat jest wysyĹ‚any
- [ ] Status cache jest raportowany

**Deliverable:** Klient z cache i obsĹ‚ugÄ… offline

---

### Etap 20: Klient - Dzwonki (3 dni)

**Cel:** Odtwarzanie dzwonkĂłw na wyĹ›wietlaczu

**Zadania:**
1. âś… Odbieranie komendy odtwarzania dzwonka (WebSocket/REST)
2. âś… Pobieranie pliku dĹşwiÄ™kowego (jeĹ›li brakuje)
3. âś… Odtwarzanie dĹşwiÄ™ku (pygame/vlc)
4. âś… Konfiguracja gĹ‚oĹ›noĹ›ci
5. âś… Logowanie odtworzenia
6. âś… ObsĹ‚uga bĹ‚Ä™dĂłw (brak pliku, brak audio)

**Weryfikacja:**
- [ ] Dzwonek jest odtwarzany o wĹ‚aĹ›ciwym czasie
- [ ] GĹ‚oĹ›noĹ›Ä‡ jest poprawna
- [ ] BĹ‚Ä™dy sÄ… obsĹ‚ugiwane
- [ ] Logowanie dziaĹ‚a

**Deliverable:** Klient z obsĹ‚ugÄ… dzwonkĂłw

---

### Etap 21: Integracja Google Drive (1 tydzieĹ„)

**Cel:** Integracja z Google Drive (folder ZASTÄPSTWA)

**Zadania:**
1. âś… Konfiguracja OAuth 2.0 (Google)
2. âś… Endpoint autoryzacji
3. âś… WybĂłr folderu ZASTÄPSTWA
4. âś… Monitorowanie zmian (webhook + polling)
5. âś… Automatyczne pobieranie plikĂłw
6. âś… Upload do systemu
7. âś… Automatyczne tworzenie harmonogramĂłw (opcjonalnie)
8. âś… Tabela cloud_sync i cloud_files

**Weryfikacja:**
- [ ] MoĹĽna autoryzowaÄ‡ Google Drive (admin)
- [ ] MoĹĽna wybraÄ‡ folder ZASTÄPSTWA
- [ ] Zmiany sÄ… wykrywane
- [ ] Pliki sÄ… automatycznie pobierane
- [ ] Pliki sÄ… uploadowane do systemu

**Deliverable:** Integracja Google Drive

---

### Etap 22: Dzielenie DĹ‚ugich Excel (1 tydzieĹ„)

**Cel:** Dzielenie dĹ‚ugich plikĂłw Excel na grupy monitorĂłw pionowych

**Zadania:**
1. âś… Analiza pliku Excel (liczba wierszy)
2. âś… Algorytm podziaĹ‚u wierszy
3. âś… Renderowanie czÄ™Ĺ›ci dla kaĹĽdego wyĹ›wietlacza
4. âś… Zapis jako osobne "wersje" treĹ›ci
5. âś… Metadata z konfiguracjÄ… podziaĹ‚u
6. âś… Klient pobiera odpowiedniÄ… wersjÄ™

**Weryfikacja:**
- [ ] DĹ‚ugi Excel jest analizowany
- [ ] PodziaĹ‚ na czÄ™Ĺ›ci dziaĹ‚a
- [ ] KaĹĽdy wyĹ›wietlacz w grupie otrzymuje swojÄ… czÄ™Ĺ›Ä‡
- [ ] Renderowanie dziaĹ‚a poprawnie
- [ ] Klient wyĹ›wietla wĹ‚aĹ›ciwÄ… czÄ™Ĺ›Ä‡

**Deliverable:** System dzielenia dĹ‚ugich Excel

---

### Etap 23: Graficzny Edytor UkĹ‚adu (1 tydzieĹ„)

**Cel:** Graficzny edytor ukĹ‚adu monitorĂłw

**Zadania:**
1. âś… Wizualizacja budynku (piÄ™tra)
2. âś… Drag & drop wyĹ›wietlaczy
3. âś… Konfiguracja pozycji (x, y)
4. âś… Konfiguracja grup (pionowe 3x)
5. âś… Zapis konfiguracji (JSON)
6. âś… Walidacja ukĹ‚adu

**Weryfikacja:**
- [ ] MoĹĽna przeciÄ…gnÄ…Ä‡ wyĹ›wietlacz na wizualizacjÄ™
- [ ] Pozycja jest zapisywana
- [ ] Grupy sÄ… konfigurowane
- [ ] Konfiguracja jest zapisywana

**Deliverable:** Graficzny edytor ukĹ‚adu

---

### Etap 24: Symulacja WyĹ›wietlania (1 tydzieĹ„)

**Cel:** Publiczna strona symulacji wyĹ›wietlania

**Zadania:**
1. âś… Publiczna strona /simulation (bez logowania)
2. âś… Wizualizacja wszystkich wyĹ›wietlaczy
3. âś… PodglÄ…d aktualnej treĹ›ci na kaĹĽdym monitorze
4. âś… Status online/offline
5. âś… WebSocket dla aktualizacji (publiczny, read-only)
6. âś… Przewijanie miÄ™dzy piÄ™trami
7. âś… Zoom na monitor

**Weryfikacja:**
- [ ] Strona jest dostÄ™pna bez logowania
- [ ] Wizualizacja pokazuje wszystkie wyĹ›wietlacze
- [ ] PodglÄ…d treĹ›ci dziaĹ‚a
- [ ] Status jest aktualizowany w czasie rzeczywistym
- [ ] Przewijanie i zoom dziaĹ‚ajÄ…

**Deliverable:** Publiczna strona symulacji

---

### Etap 25: Testy i Optymalizacja (1 tydzieĹ„)

**Cel:** Testy caĹ‚ego systemu i optymalizacja

**Zadania:**
1. âś… Testy integracyjne
2. âś… Testy wydajnoĹ›ciowe
3. âś… Testy obciÄ…ĹĽeniowe (10 wyĹ›wietlaczy)
4. âś… Optymalizacja zapytaĹ„ do bazy
5. âś… Optymalizacja cache
6. âś… Naprawa bĹ‚Ä™dĂłw
7. âś… Dokumentacja uĹĽytkownika

**Weryfikacja:**
- [ ] Wszystkie funkcje dziaĹ‚ajÄ…
- [ ] System obsĹ‚uguje 10 wyĹ›wietlaczy
- [ ] WydajnoĹ›Ä‡ jest akceptowalna
- [ ] BĹ‚Ä™dy sÄ… naprawione
- [ ] Dokumentacja jest kompletna

**Deliverable:** Gotowy system do wdroĹĽenia

---

## 12. Harmonogram Implementacji (Szacunkowy)

| Etap | Nazwa | Czas | ZaleĹĽnoĹ›ci |
|------|-------|------|------------|
| 0 | Przygotowanie Ĺ›rodowiska | 1 tydzieĹ„ | - |
| 1 | Backend API - Podstawy | 1 tydzieĹ„ | 0 |
| 2 | Backend - WyĹ›wietlacze | 3 dni | 1 |
| 3 | Backend - Upload treĹ›ci | 1 tydzieĹ„ | 1 |
| 4 | Backend - Transkodowanie video | 3 dni | 3 |
| 5 | Backend - Harmonogramy | 1 tydzieĹ„ | 3 |
| 6 | Backend - Grupowanie | 3 dni | 2, 5 |
| 7 | Backend - Monitoring | 1 tydzieĹ„ | 2 |
| 8 | Backend - Raportowanie | 3 dni | 7 |
| 9 | Backend - Dzwonki | 1 tydzieĹ„ | 1 |
| 10 | Frontend - Podstawy | 1 tydzieĹ„ | 1 |
| 11 | Frontend - WyĹ›wietlacze | 1 tydzieĹ„ | 10, 2 |
| 12 | Frontend - Status | 1 tydzieĹ„ | 10, 7 |
| 13 | Frontend - Upload | 1 tydzieĹ„ | 10, 3 |
| 14 | Frontend - Harmonogramy | 1 tydzieĹ„ | 10, 5 |
| 15 | Frontend - Raporty | 3 dni | 10, 8 |
| 16 | Frontend - Dzwonki | 1 tydzieĹ„ | 10, 9 |
| 17 | Klient - Podstawy | 1 tydzieĹ„ | 1, 2 |
| 18 | Klient - Formaty | 1 tydzieĹ„ | 17, 3 |
| 19 | Klient - Cache | 1 tydzieĹ„ | 17, 5 |
| 20 | Klient - Dzwonki | 3 dni | 17, 9 |
| 21 | Google Drive | 1 tydzieĹ„ | 3 |
| 22 | Dzielenie Excel | 1 tydzieĹ„ | 3, 6 |
| 23 | Edytor ukĹ‚adu | 1 tydzieĹ„ | 10, 6 |
| 24 | Symulacja | 1 tydzieĹ„ | 10, 12 |
| 25 | Testy i optymalizacja | 1 tydzieĹ„ | Wszystkie |

**CaĹ‚kowity czas:** ~20-22 tygodni (5-6 miesiÄ™cy)

**MoĹĽliwoĹ›Ä‡ rĂłwnolegĹ‚ej pracy:**
- Etapy 10-16 (Frontend) mogÄ… byÄ‡ rĂłwnolegĹ‚e z 17-20 (Klient)
- Etapy 21-24 mogÄ… byÄ‡ rĂłwnolegĹ‚e

---

## 13. Metodyka Weryfikacji EtapĂłw

### Dla kaĹĽdego etapu:

1. **Checklist weryfikacji** - lista punktĂłw do sprawdzenia
2. **Testy manualne** - scenariusze testowe
3. **Testy API** - curl/Postman
4. **Testy integracyjne** - poĹ‚Ä…czenie komponentĂłw
5. **Code review** - przeglÄ…d kodu

### PrzykĹ‚adowy proces weryfikacji:

1. **Przygotowanie:**
   - Sprawdzenie czy wszystkie zaleĹĽnoĹ›ci sÄ… speĹ‚nione
   - Przygotowanie Ĺ›rodowiska testowego

2. **Testy funkcjonalne:**
   - Wykonanie wszystkich scenariuszy z checklist
   - Sprawdzenie czy wszystkie funkcje dziaĹ‚ajÄ…

3. **Testy niefunkcjonalne:**
   - WydajnoĹ›Ä‡
   - BezpieczeĹ„stwo
   - ObsĹ‚uga bĹ‚Ä™dĂłw

4. **Dokumentacja:**
   - Aktualizacja dokumentacji
   - Notatki z testĂłw

5. **Zatwierdzenie:**
   - Zatwierdzenie przez zespĂłĹ‚
   - PrzejĹ›cie do nastÄ™pnego etapu

---

**Gotowe do implementacji etapowej!** đźš€

### Faza 1: MVP (MIN-imum)
1. Backend API (FastAPI)
2. Baza danych (PostgreSQL)
3. Panel webowy (React) - podstawowy
4. Upload treĹ›ci (PDF, Excel, obrazy, video)
5. Transkodowanie video (FFmpeg)
6. Klient wyĹ›wietlacza (Python + PyQt6)
7. Podstawowe harmonogramy
8. Grupowanie wyĹ›wietlaczy (proste)
9. ObsĹ‚uga rotacji 90Â°

**Czas: ~6-8 tygodni**

### Faza 2: Rozszerzenia
1. Integracja Google Drive
2. Dzielenie dĹ‚ugich plikĂłw Excel
3. Graficzny edytor ukĹ‚adu
4. Symulacja wyĹ›wietlania
5. Harmonogramy wĹ‚Ä…czania TV (podstawowe)
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
1. **Harmonogramy TV**: Czy potrzebne rĂłĹĽne czasy dla rĂłĹĽnych dni tygodnia? (np. weekendy)
2. **Dzielenie Excel**: Czy zawsze dzieliÄ‡ rĂłwno, czy moĹĽliwoĹ›Ä‡ rÄ™cznej konfiguracji zakresĂłw?
3. **Video**: Czy potrzebne rĂłĹĽne wersje jakoĹ›ciowe dla rĂłĹĽnych wyĹ›wietlaczy?
4. **Backup**: Jak czÄ™sto i gdzie przechowywaÄ‡?
5. **Monitoring**: Czy potrzebne powiadomienia email/SMS przy bĹ‚Ä™dach?

### Zalecenia:
- RozpoczÄ™cie od MVP (Faza 1)
- Testowanie na 1-2 wyĹ›wietlaczach przed peĹ‚nym wdroĹĽeniem
- Dokumentacja dla operatora (jak uĹĽywaÄ‡ panelu)
- Backup przed kaĹĽdÄ… wiÄ™kszÄ… zmianÄ…

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
| Serwer plikĂłw | Nginx |
| System klienta | Ubuntu/Debian + systemd |

---

**Gotowe do implementacji!** đźš€


