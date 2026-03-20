# Plan Realizacji (na później): Launcher VPN + Panel Salonu

## Cel
Uprościć dostęp do panelu operacyjnego dla salonu: użytkownik klika jedną ikonę, aplikacja uruchamia tunel WireGuard (jeśli nieaktywny), sprawdza dostępność i otwiera panel w przeglądarce.

## Kontekst
- Kierunek architektury: niezależność od firm trzecich, VPN oparty o self-hosted WireGuard.
- Public booking pozostaje publiczny.
- Panel operacyjny i API operacyjne mają być dostępne tylko przez VPN.
- Temat odłożony, aby nie zaburzać bieżącego developmentu aplikacji.

## Zakres (MVP)
1. Launcher desktop dla stanowisk salonowych (Windows).
2. Jedna akcja użytkownika: "Otwórz Panel".
3. Kroki automatyczne:
- sprawdzenie internetu,
- sprawdzenie czy tunel WG jest aktywny,
- aktywacja tunelu (jeśli nieaktywny),
- walidacja dostępu do panelu (health/check URL),
- otwarcie panelu w domyślnej przeglądarce.
4. Czytelne komunikaty błędów i statusów.
5. Log lokalny (diagnostyka wsparcia).

## Poza zakresem (na MVP)
- Auto-update launchera.
- Centralna telemetria i zdalne zarządzanie.
- Integracja SSO.
- Wersje mobilne launchera.

## Użytkownik i UX
### Docelowy flow
1. Pracownik klika ikonę `Panel Salonu`.
2. Launcher pokazuje status: `Sprawdzam połączenie...`.
3. Jeśli VPN jest wyłączony, launcher uruchamia tunel.
4. Po potwierdzeniu, że panel jest osiągalny, launcher otwiera `https://panel.internal`.
5. Jeśli coś nie działa, użytkownik dostaje jasny komunikat i numer błędu.

### Minimalne komunikaty
- `Brak internetu.`
- `Uruchamianie bezpiecznego połączenia VPN...`
- `Połączenie VPN aktywne.`
- `Nie można uruchomić VPN. Skontaktuj się z administratorem.`
- `Panel chwilowo niedostępny.`

## Wymagania techniczne
### Środowisko
- Stanowiska: Windows (recepcja/salon).
- WireGuard zainstalowany lokalnie.
- Profil WG dostarczony per stanowisko/per salon.

### Integracja z WireGuard
- Preferowany tryb: tunel jako usługa systemowa (stabilniejszy niż sesyjny).
- Alternatywa: uruchamianie tunelu z launchera.
- Launcher musi mieć mechanizm wykrywania stanu tunelu i timeout (np. 20-30 s).

### Endpointy kontrolne
- VPN check: adres wewnętrzny (np. DNS prywatny lub IP w sieci WG).
- Panel check: `GET /health` backendu operacyjnego.

## Architektura bezpieczeństwa (docelowa)
1. Publicznie wystawione tylko:
- `frontend_public`,
- `backend_public`.
2. Niepubliczne (tylko VPN):
- `frontend` (panel),
- `backend` (API operacyjne),
- SSH administracyjne.
3. Firewall:
- zezwala publicznie jedynie na port WireGuard (`UDP 51820`) i public booking,
- blokuje dostęp do panelu z internetu.

## Warianty implementacji launchera
### Wariant A (start, najprostszy)
- Skrypt PowerShell + skrót na pulpicie.
- Plusy: szybkie wdrożenie, niski koszt.
- Minus: gorszy UX, trudniejsza dystrybucja zmian.

### Wariant B (docelowy)
- Lekki launcher GUI (np. .NET lub Tauri).
- Plusy: lepszy UX, czytelny status, łatwiejsze wsparcie.
- Minus: większy nakład początkowy.

## Plan etapowy
### Etap 0: Przygotowanie
- Ustalić docelowy adres panelu wewnętrznego (`panel.internal`).
- Ustalić standard profili WireGuard (nazwa, rotacja kluczy, owner).
- Przygotować checklistę instalacji stanowiska.

### Etap 1: MVP techniczne
- Wdrożyć wariant A (skrypt + skrót).
- Pilot na 1 salonie.
- Zbieranie błędów operacyjnych (2-4 tygodnie).

### Etap 2: Launcher GUI
- Implementacja wariantu B z tym samym flow.
- Migracja salonów etapami.

### Etap 3: Utrwalenie operacyjne
- Procedura onboardingu nowego stanowiska.
- Procedura awaryjna (fallback przy awarii VPN).
- Rotacja kluczy i audyt dostępu.

## Kryteria akceptacji
1. Użytkownik uruchamia panel jednym kliknięciem.
2. Bez aktywnego VPN panel operacyjny jest niedostępny z internetu.
3. Czas gotowości od kliknięcia do otwarcia panelu: <= 10 s (typowo), <= 30 s (cold start).
4. Komunikaty błędów są zrozumiałe dla nietechnicznego pracownika.
5. Wsparcie techniczne ma log wystarczający do diagnozy problemu.

## Ryzyka i mitigacje
- Ryzyko: błędy uprawnień do startu tunelu.
  Mitigacja: tunel jako usługa systemowa + instalator stanowiskowy.
- Ryzyko: pracownik pracuje bez VPN.
  Mitigacja: panel niedostępny poza VPN (hard enforcement sieciowy).
- Ryzyko: utrata klucza stanowiska.
  Mitigacja: szybka revokacja peer + re-issuance klucza.

## Decyzje do podjęcia przed realizacją
1. Docelowy stack launchera: PowerShell-only vs GUI.
2. Model dystrybucji: ręczny vs centralny (GPO/MDM).
3. Polityka kluczy: per stanowisko czy per salon.
4. Format supportu: czy wdrażamy kody błędów i instrukcję dla recepcji.

## Status
- Dokument przygotowany jako backlog item do realizacji później.
- Brak wdrożenia kodowego launchera na tym etapie.
