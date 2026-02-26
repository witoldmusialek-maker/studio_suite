# Studio Suite Android Client

Klient Android dla systemu Studio Suite - wyĹ›wietlacz treĹ›ci zarzÄ…dzany zdalnie.

## Funkcje

- **Rejestracja automatyczna** - urzÄ…dzenie rejestruje siÄ™ na serwerze przez MAC adres
- **WyĹ›wietlanie treĹ›ci** - obrazy, video, PDF
- **Harmonogramy** - automatyczna zmiana treĹ›ci wedĹ‚ug harmonogramu
- **Heartbeat** - regularne aktualizacje statusu
- **Cache lokalny** - treĹ›ci sÄ… cache'owane dla szybkoĹ›ci
- **Dzwonki** - odtwarzanie dĹşwiÄ™kĂłw dzwonka szkolnego
- **Kiosk mode** - aplikacja moĹĽe dziaĹ‚aÄ‡ jako launcher
- **Autostart** - uruchamia siÄ™ automatycznie po starcie urzÄ…dzenia

## Wymagania

- Android 5.0 (API 21) lub nowszy
- Serwer Studio Suite (backend API)

## Budowanie

### Wymagania

- Android Studio Hedgehog lub nowszy
- JDK 17
- Android SDK 34

### Kroki

1. OtwĂłrz projekt w Android Studio:
   ```
   studio_suite/android-client/
   ```

2. Poczekaj na synchronizacjÄ™ Gradle

3. Wybierz konfiguracjÄ™ `app` i kliknij Run

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

Przy pierwszym uruchomieniu wprowadĹş adres serwera:
```
http://192.168.1.100:8000/api/v1/
```

Dla emulatora Android:
```
http://10.0.2.2:8000/api/v1/
```

### Kiosk Mode

Aby uruchomiÄ‡ aplikacjÄ™ jako launcher (kiosk mode):

1. Ustaw aplikacjÄ™ jako domyĹ›lny launcher
2. UrzÄ…dzenie bÄ™dzie automatycznie uruchamiaÄ‡ aplikacjÄ™ po starcie

### Uprawnienia

Aplikacja wymaga nastÄ™pujÄ…cych uprawnieĹ„:
- `INTERNET` - komunikacja z serwerem
- `ACCESS_NETWORK_STATE` - sprawdzanie poĹ‚Ä…czenia
- `RECEIVE_BOOT_COMPLETED` - autostart
- `FOREGROUND_SERVICE` - usĹ‚ugi w tle
- `SYSTEM_ALERT_WINDOW` - kiosk mode

## Architektura

```
app/
â”śâ”€â”€ src/main/java/com/digitalsignage/client/
â”‚   â”śâ”€â”€ data/
â”‚   â”‚   â”śâ”€â”€ api/          # Retrofit API
â”‚   â”‚   â”śâ”€â”€ cache/        # ZarzÄ…dzanie cache
â”‚   â”‚   â”śâ”€â”€ model/        # Data classes
â”‚   â”‚   â””â”€â”€ repository/   # Repository pattern
â”‚   â”śâ”€â”€ di/               # Hilt DI
â”‚   â”śâ”€â”€ receiver/         # BootReceiver
â”‚   â”śâ”€â”€ ui/
â”‚   â”‚   â”śâ”€â”€ components/   # Composable components
â”‚   â”‚   â”śâ”€â”€ screen/       # Ekrany
â”‚   â”‚   â”śâ”€â”€ theme/        # Motyw
â”‚   â”‚   â””â”€â”€ viewmodel/    # ViewModels
â”‚   â”śâ”€â”€ util/             # NarzÄ™dzia
â”‚   â”śâ”€â”€ DigitalSignageApp.kt
â”‚   â””â”€â”€ MainActivity.kt
â””â”€â”€ src/main/res/
    â””â”€â”€ values/
        â”śâ”€â”€ strings.xml
        â””â”€â”€ themes.xml
```

## Technologie

- **Kotlin** - jÄ™zyk programowania
- **Jetpack Compose** - UI
- **Hilt** - dependency injection
- **Retrofit** - komunikacja HTTP
- **OkHttp** - HTTP client
- **Coil** - Ĺ‚adowanie obrazĂłw
- **ExoPlayer** - odtwarzanie video
- **DataStore** - preferencje
- **Coroutines** - asynchronicznoĹ›Ä‡

## API Endpoints

Klient komunikuje siÄ™ z nastÄ™pujÄ…cymi endpointami:

| Endpoint | Metoda | Opis |
|----------|--------|------|
| `/displays/register` | POST | Rejestracja wyĹ›wietlacza |
| `/displays/{id}/heartbeat` | POST | Heartbeat |
| `/schedules/display/{id}/schedule` | GET | Pobranie harmonogramu |
| `/content/{id}` | GET | Informacje o treĹ›ci |
| `/content/{id}/download` | GET | Pobranie pliku |
| `/bells/play-command/{id}` | GET | Komenda dzwonka |

## RozwiÄ…zywanie problemĂłw

### Aplikacja nie Ĺ‚Ä…czy siÄ™ z serwerem

1. SprawdĹş czy urzÄ…dzenie jest w tej samej sieci co serwer
2. SprawdĹş czy adres serwera jest poprawny
3. SprawdĹş czy serwer jest dostÄ™pny (ping)
4. SprawdĹş firewall

### TreĹ›ci siÄ™ nie wyĹ›wietlajÄ…

1. SprawdĹş czy harmonogram jest skonfigurowany na serwerze
2. SprawdĹş status poĹ‚Ä…czenia (zielona kropka = OK)
3. SprawdĹş logi aplikacji

### Video nie odtwarza

1. SprawdĹş czy format jest obsĹ‚ugiwany (MP4 H.264)
2. SprawdĹş czy plik nie jest uszkodzony
3. SprawdĹş logi ExoPlayer

## Licencja

Projekt wewnÄ™trzny - do uĹĽytku w szkole.

