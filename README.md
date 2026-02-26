# Studio Suite

System zarzÄ…dzania treĹ›ciÄ… dla wyĹ›wietlaczy informacyjnych w szkole.

## Opis

System skĹ‚ada siÄ™ z:
- **Serwer** (Ubuntu VM na Hyper-V) - backend API i panel zarzÄ…dzajÄ…cy
- **WyĹ›wietlacze** (HP T630 z Linuxem) - klienci wyĹ›wietlajÄ…ce treĹ›ci

## Funkcje

- âś… WyĹ›wietlanie treĹ›ci (PDF, Excel, obrazy, video)
- âś… Harmonogramy wyĹ›wietlania
- âś… Grupowanie wyĹ›wietlaczy
- âś… Monitoring statusu w czasie rzeczywistym
- âś… System dzwonkĂłw szkolnych
- âś… Integracja z Google Drive (folder ZASTÄPSTWA)
- âś… Raportowanie i alerty

## Struktura Projektu

```
studio_suite/
â”śâ”€â”€ backend/          # Backend API (FastAPI) âś…
â”śâ”€â”€ frontend/         # Panel webowy (React) đź”„
â”śâ”€â”€ client/           # Klient wyĹ›wietlacza (Python) âś…
â”śâ”€â”€ docs/             # Dokumentacja
â””â”€â”€ scripts/          # Skrypty pomocnicze
```

## Dokumentacja

- [Analiza i specyfikacja](ANALIZA_STUDIO_SUITE.md) - peĹ‚na analiza systemu
- [Instrukcja instalacji](studio_suite/docs/INSTALLATION.md) - jak zainstalowaÄ‡ system
- [PostÄ™p implementacji](studio_suite/PROGRESS.md) - aktualny status
- [Instrukcje kontynuacji](studio_suite/CONTINUE.md) - jak kontynuowaÄ‡ pracÄ™

## Status Implementacji

### Backend âś…
- âś… Etap 0: Przygotowanie Ĺ›rodowiska
- âś… Etap 1: Backend API - Podstawy (autentykacja, modele)
- âś… Etap 2: Backend - ZarzÄ…dzanie WyĹ›wietlaczami
- âś… Etap 3: Backend - Upload i Przetwarzanie TreĹ›ci
- âś… Etap 4: Backend - Transkodowanie Video
- âś… Etap 5: Backend - Harmonogramy TreĹ›ci
- âś… Etap 6: Backend - Grupowanie WyĹ›wietlaczy
- âś… Etap 7: Backend - Monitoring i Alerty
- âś… Etap 8: Backend - Raportowanie
- âś… Etap 9: Backend - System DzwonkĂłw

### Frontend đź”„
- âś… Etap 10: Podstawowa struktura
- âś… Etap 11: ZarzÄ…dzanie WyĹ›wietlaczami
- âś… Etap 12: Strona Statusu
- âś… Etap 13: Upload TreĹ›ci (podstawowy)
- âŹł Etapy 14-16: Do zrobienia

### Klient âś…
- âś… Etap 17: Podstawowa Aplikacja (gotowa do testĂłw)

## Wymagania

- Python 3.10+
- PostgreSQL 14+
- Redis
- Node.js 18+ (dla frontendu)
- FFmpeg (dla przetwarzania video)

## Szybki Start

Zobacz [InstrukcjÄ™ instalacji](studio_suite/docs/INSTALLATION.md) dla szczegĂłĹ‚Ăłw.

### Backend

```bash
cd studio_suite/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API dostÄ™pne pod: http://localhost:8000
Dokumentacja: http://localhost:8000/docs

## Licencja

Projekt prywatny - szkoĹ‚a


