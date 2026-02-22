# Digital Signage Android TV Client

Klient Digital Signage zoptymalizowany pod kątem urządzeń Android TV (Chromecast z Google TV, NVIDIA Shield, Xiaomi Mi Box, Sony TV, Philips TV itp.).

## Funkcje

- Wyświetlanie treści (obrazy, wideo) na telewizorach
- Automatyczna rejestracja w systemie Digital Signage
- Obsługa treści testowych i harmonogramów
- Automatyczne uruchamianie po starcie urządzenia
- Tryb pełnoekranowy z ukrytymi paskami systemowymi
- Zoptymalizowane UI dla dużych ekranów (TV)

## Wymagania

- Android TV 5.0 (Lollipop) lub nowszy
- Połączenie sieciowe z serwerem Digital Signage

## Instalacja

### Metoda 1: ADB (zalecana)

```bash
# Włącz debugowanie ADB na urządzeniu TV
# Ustawienia -> O urządzeniu -> Kliknij 7 razy na "Kompilacja"
# Ustawienia -> Opcje programistyczne -> Debugowanie USB -> Włączone

# Pobierz adres IP urządzenia TV
# Ustawienia -> Sieć i Internet -> Wi-Fi -> Kliknij na sieć -> Adres IP

# Połącz przez ADB
adb connect <IP_TV>:5555

# Zainstaluj APK
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

### Metoda 2: Pobieranie z serwera

1. Skopiuj APK na serwer HTTP
2. Otwórz przeglądarkę na TV (Chrome)
3. Pobierz plik APK
4. Kliknij aby zainstalować (wymagane włączenie "Nieznane źródła")

## Konfiguracja

1. **Uruchom aplikację** - Wyświetli się ekran konfiguracji
2. **Wprowadź adres serwera** - np. `http://192.168.1.100:8000/api/v1/`
3. **Kliknij OK na pilocie** - Aplikacja połączy się z serwerem
4. **Zarejestruj urządzenie** - ID wyświetlacza zostanie przypisane automatycznie

## Znane urządzenia kompatybilne

| Urządzenie | Status | Uwagi |
|------------|--------|-------|
| Chromecast z Google TV | ✅ Pełna obsługa | Wymagane włączenie ADB |
| NVIDIA Shield TV | ✅ Pełna obsługa | Wszystkie funkcje |
| Xiaomi Mi Box / Mi TV | ✅ Pełna obsługa | Standardowa instalacja |
| Sony Android TV | ✅ Pełna obsługa | Wymaga włączenia nieznanych źródeł |
| Philips Android TV | ✅ Pełna obsługa | Standardowa instalacja |
| Amazon Fire TV Stick | ✅ Pełna obsługa | Sideload przez ADB |
| Samsung Tizen TV | ❌ Nieobsługiwane | Nie jest Android TV |
| LG webOS TV | ❌ Nieobsługiwane | Nie jest Android TV |
| Klasyczny Chromecast | ❌ Nieobsługiwane | Brak możliwości instalacji |

## Różnice względem klienta mobilnego

- **UI**: Dużo większe elementy widoczne z odległości 2-3m
- **Orientacja**: Tylko tryb poziomy (landscape)
- **Nawigacja**: Obsługa pilota D-pad
- **Automatyczny start**: Uruchamia się po boot urządzenia

## Budowanie

```bash
# Debug
.\gradlew.bat assembleDebug

# Release
.\gradlew.bat assembleRelease
```

## Licencja

Projekt wewnętrzny Digital Signage.