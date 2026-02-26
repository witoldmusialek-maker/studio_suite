# Studio Suite Android TV Client

Klient Studio Suite zoptymalizowany pod kÄ…tem urzÄ…dzeĹ„ Android TV (Chromecast z Google TV, NVIDIA Shield, Xiaomi Mi Box, Sony TV, Philips TV itp.).

## Funkcje

- WyĹ›wietlanie treĹ›ci (obrazy, wideo) na telewizorach
- Automatyczna rejestracja w systemie Studio Suite
- ObsĹ‚uga treĹ›ci testowych i harmonogramĂłw
- Automatyczne uruchamianie po starcie urzÄ…dzenia
- Tryb peĹ‚noekranowy z ukrytymi paskami systemowymi
- Zoptymalizowane UI dla duĹĽych ekranĂłw (TV)

## Wymagania

- Android TV 5.0 (Lollipop) lub nowszy
- PoĹ‚Ä…czenie sieciowe z serwerem Studio Suite

## Instalacja

### Metoda 1: ADB (zalecana)

```bash
# WĹ‚Ä…cz debugowanie ADB na urzÄ…dzeniu TV
# Ustawienia -> O urzÄ…dzeniu -> Kliknij 7 razy na "Kompilacja"
# Ustawienia -> Opcje programistyczne -> Debugowanie USB -> WĹ‚Ä…czone

# Pobierz adres IP urzÄ…dzenia TV
# Ustawienia -> SieÄ‡ i Internet -> Wi-Fi -> Kliknij na sieÄ‡ -> Adres IP

# PoĹ‚Ä…cz przez ADB
adb connect <IP_TV>:5555

# Zainstaluj APK
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

### Metoda 2: Pobieranie z serwera

1. Skopiuj APK na serwer HTTP
2. OtwĂłrz przeglÄ…darkÄ™ na TV (Chrome)
3. Pobierz plik APK
4. Kliknij aby zainstalowaÄ‡ (wymagane wĹ‚Ä…czenie "Nieznane ĹşrĂłdĹ‚a")

## Konfiguracja

1. **Uruchom aplikacjÄ™** - WyĹ›wietli siÄ™ ekran konfiguracji
2. **WprowadĹş adres serwera** - np. `http://192.168.1.100:8000/api/v1/`
3. **Kliknij OK na pilocie** - Aplikacja poĹ‚Ä…czy siÄ™ z serwerem
4. **Zarejestruj urzÄ…dzenie** - ID wyĹ›wietlacza zostanie przypisane automatycznie

## Znane urzÄ…dzenia kompatybilne

| UrzÄ…dzenie | Status | Uwagi |
|------------|--------|-------|
| Chromecast z Google TV | âś… PeĹ‚na obsĹ‚uga | Wymagane wĹ‚Ä…czenie ADB |
| NVIDIA Shield TV | âś… PeĹ‚na obsĹ‚uga | Wszystkie funkcje |
| Xiaomi Mi Box / Mi TV | âś… PeĹ‚na obsĹ‚uga | Standardowa instalacja |
| Sony Android TV | âś… PeĹ‚na obsĹ‚uga | Wymaga wĹ‚Ä…czenia nieznanych ĹşrĂłdeĹ‚ |
| Philips Android TV | âś… PeĹ‚na obsĹ‚uga | Standardowa instalacja |
| Amazon Fire TV Stick | âś… PeĹ‚na obsĹ‚uga | Sideload przez ADB |
| Samsung Tizen TV | âťŚ NieobsĹ‚ugiwane | Nie jest Android TV |
| LG webOS TV | âťŚ NieobsĹ‚ugiwane | Nie jest Android TV |
| Klasyczny Chromecast | âťŚ NieobsĹ‚ugiwane | Brak moĹĽliwoĹ›ci instalacji |

## RĂłĹĽnice wzglÄ™dem klienta mobilnego

- **UI**: DuĹĽo wiÄ™ksze elementy widoczne z odlegĹ‚oĹ›ci 2-3m
- **Orientacja**: Tylko tryb poziomy (landscape)
- **Nawigacja**: ObsĹ‚uga pilota D-pad
- **Automatyczny start**: Uruchamia siÄ™ po boot urzÄ…dzenia

## Budowanie

```bash
# Debug
.\gradlew.bat assembleDebug

# Release
.\gradlew.bat assembleRelease
```

## Licencja

Projekt wewnÄ™trzny Studio Suite.
