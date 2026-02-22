# Digital Signage Android Client

Klient Android dla systemu Digital Signage - wyświetlacz treści zarządzany zdalnie.

## Funkcje

- **Rejestracja automatyczna** - urządzenie rejestruje się na serwerze przez MAC adres
- **Wyświetlanie treści** - obrazy, video, PDF
- **Harmonogramy** - automatyczna zmiana treści według harmonogramu
- **Heartbeat** - regularne aktualizacje statusu
- **Cache lokalny** - treści są cache'owane dla szybkości
- **Dzwonki** - odtwarzanie dźwięków dzwonka szkolnego
- **Kiosk mode** - aplikacja może działać jako launcher
- **Autostart** - uruchamia się automatycznie po starcie urządzenia

## Wymagania

- Android 5.0 (API 21) lub nowszy
- Serwer Digital Signage (backend API)

## Budowanie

### Wymagania

- Android Studio Hedgehog lub nowszy
- JDK 17
- Android SDK 34

### Kroki

1. Otwórz projekt w Android Studio:
   ```
   digital_signage/android-client/
   ```

2. Poczekaj na synchronizację Gradle

3. Wybierz konfigurację `app` i kliknij Run

### Build APK

```bash
./gradlew assembleDebug
```

APK znajdziesz w: `app/build/outputs/apk/debug/app-debug.apk`

### Build Release

```bash
./gradlew assembleRelease
```

## Konfiguracja

### Adres serwera

Przy pierwszym uruchomieniu wprowadź adres serwera:
```
http://192.168.1.100:8000/api/v1/
```

Dla emulatora Android:
```
http://10.0.2.2:8000/api/v1/
```

### Kiosk Mode

Aby uruchomić aplikację jako launcher (kiosk mode):

1. Ustaw aplikację jako domyślny launcher
2. Urządzenie będzie automatycznie uruchamiać aplikację po starcie

### Uprawnienia

Aplikacja wymaga następujących uprawnień:
- `INTERNET` - komunikacja z serwerem
- `ACCESS_NETWORK_STATE` - sprawdzanie połączenia
- `RECEIVE_BOOT_COMPLETED` - autostart
- `FOREGROUND_SERVICE` - usługi w tle
- `SYSTEM_ALERT_WINDOW` - kiosk mode

## Architektura

```
app/
├── src/main/java/com/digitalsignage/client/
│   ├── data/
│   │   ├── api/          # Retrofit API
│   │   ├── cache/        # Zarządzanie cache
│   │   ├── model/        # Data classes
│   │   └── repository/   # Repository pattern
│   ├── di/               # Hilt DI
│   ├── receiver/         # BootReceiver
│   ├── ui/
│   │   ├── components/   # Composable components
│   │   ├── screen/       # Ekrany
│   │   ├── theme/        # Motyw
│   │   └── viewmodel/    # ViewModels
│   ├── util/             # Narzędzia
│   ├── DigitalSignageApp.kt
│   └── MainActivity.kt
└── src/main/res/
    └── values/
        ├── strings.xml
        └── themes.xml
```

## Technologie

- **Kotlin** - język programowania
- **Jetpack Compose** - UI
- **Hilt** - dependency injection
- **Retrofit** - komunikacja HTTP
- **OkHttp** - HTTP client
- **Coil** - ładowanie obrazów
- **ExoPlayer** - odtwarzanie video
- **DataStore** - preferencje
- **Coroutines** - asynchroniczność

## API Endpoints

Klient komunikuje się z następującymi endpointami:

| Endpoint | Metoda | Opis |
|----------|--------|------|
| `/displays/register` | POST | Rejestracja wyświetlacza |
| `/displays/{id}/heartbeat` | POST | Heartbeat |
| `/schedules/display/{id}/schedule` | GET | Pobranie harmonogramu |
| `/content/{id}` | GET | Informacje o treści |
| `/content/{id}/download` | GET | Pobranie pliku |
| `/bells/play-command/{id}` | GET | Komenda dzwonka |

## Rozwiązywanie problemów

### Aplikacja nie łączy się z serwerem

1. Sprawdź czy urządzenie jest w tej samej sieci co serwer
2. Sprawdź czy adres serwera jest poprawny
3. Sprawdź czy serwer jest dostępny (ping)
4. Sprawdź firewall

### Treści się nie wyświetlają

1. Sprawdź czy harmonogram jest skonfigurowany na serwerze
2. Sprawdź status połączenia (zielona kropka = OK)
3. Sprawdź logi aplikacji

### Video nie odtwarza

1. Sprawdź czy format jest obsługiwany (MP4 H.264)
2. Sprawdź czy plik nie jest uszkodzony
3. Sprawdź logi ExoPlayer

## Licencja

Projekt wewnętrzny - do użytku w szkole.