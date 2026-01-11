# System Digital Signage

System zarządzania treścią dla wyświetlaczy informacyjnych w szkole.

## Opis

System składa się z:
- **Serwer** (Ubuntu VM na Hyper-V) - backend API i panel zarządzający
- **Wyświetlacze** (HP T630 z Linuxem) - klienci wyświetlające treści

## Funkcje

- ✅ Wyświetlanie treści (PDF, Excel, obrazy, video)
- ✅ Harmonogramy wyświetlania
- ✅ Grupowanie wyświetlaczy
- ✅ Monitoring statusu w czasie rzeczywistym
- ✅ System dzwonków szkolnych
- ✅ Integracja z Google Drive (folder ZASTĘPSTWA)
- ✅ Raportowanie i alerty

## Struktura Projektu

```
digital_signage/
├── backend/          # Backend API (FastAPI) ✅
├── frontend/         # Panel webowy (React) 🔄
├── client/           # Klient wyświetlacza (Python) ✅
├── docs/             # Dokumentacja
└── scripts/          # Skrypty pomocnicze
```

## Dokumentacja

- [Analiza i specyfikacja](ANALIZA_DIGITAL_SIGNAGE.md) - pełna analiza systemu
- [Instrukcja instalacji](digital_signage/docs/INSTALLATION.md) - jak zainstalować system
- [Postęp implementacji](digital_signage/PROGRESS.md) - aktualny status
- [Instrukcje kontynuacji](digital_signage/CONTINUE.md) - jak kontynuować pracę

## Status Implementacji

### Backend ✅
- ✅ Etap 0: Przygotowanie środowiska
- ✅ Etap 1: Backend API - Podstawy (autentykacja, modele)
- ✅ Etap 2: Backend - Zarządzanie Wyświetlaczami
- ✅ Etap 3: Backend - Upload i Przetwarzanie Treści
- ✅ Etap 4: Backend - Transkodowanie Video
- ✅ Etap 5: Backend - Harmonogramy Treści
- ✅ Etap 6: Backend - Grupowanie Wyświetlaczy
- ✅ Etap 7: Backend - Monitoring i Alerty
- ✅ Etap 8: Backend - Raportowanie
- ✅ Etap 9: Backend - System Dzwonków

### Frontend 🔄
- ✅ Etap 10: Podstawowa struktura
- ✅ Etap 11: Zarządzanie Wyświetlaczami
- ✅ Etap 12: Strona Statusu
- ✅ Etap 13: Upload Treści (podstawowy)
- ⏳ Etapy 14-16: Do zrobienia

### Klient ✅
- ✅ Etap 17: Podstawowa Aplikacja (gotowa do testów)

## Wymagania

- Python 3.10+
- PostgreSQL 14+
- Redis
- Node.js 18+ (dla frontendu)
- FFmpeg (dla przetwarzania video)

## Szybki Start

Zobacz [Instrukcję instalacji](digital_signage/docs/INSTALLATION.md) dla szczegółów.

### Backend

```bash
cd digital_signage/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API dostępne pod: http://localhost:8000
Dokumentacja: http://localhost:8000/docs

## Licencja

Projekt prywatny - szkoła
