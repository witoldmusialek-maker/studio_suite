# Rules: Zasady Projektowe Studio Suite

## 1. Cel dokumentu
Ten dokument definiuje stale zasady projektowania i wdrozen Studio Suite.
Kazda nowa funkcjonalnosc i refaktor musi byc z nimi zgodna.

## 2. Zasady architektury
1. Priorytetem jest izolacja danych tenantow i brak przeciekow miedzy tenantami.
2. Kazdy endpoint operacyjny musi byc tenant-aware:
- odczyt po `tenant_id`,
- zapis z `tenant_id`,
- walidacja dostepu do salonu i zasobu tylko w ramach tenanta.
3. Public booking pozostaje oddzielony od panelu operacyjnego.
4. Dostep do panelu operacyjnego i API operacyjnego docelowo tylko przez VPN (WireGuard).
5. Kazdy modul biznesowy musi wspierac licencjonowanie:
- brak aktywnej licencji blokuje API (`403`),
- brak aktywnej licencji ukrywa modul w UI.

## 3. Wydzielenie instancji dla jednego tenanta
Scenariusz: sprzedaz programu jednemu odbiorcy na jego serwery i domeny.

### 3.1 Model docelowy
1. Dla dedykowanego klienta uruchamiamy osobna instancje (`single-tenant deployment`):
- osobny backend,
- osobny frontend,
- osobna baza danych,
- osobny storage i backup.
2. Ten sam kod aplikacji, bez forka produktu, o ile nie ma formalnego wymagania klienta.
3. Oddzielne domeny i certyfikaty TLS klienta.
4. Oddzielne sekrety (`SECRET_KEY`, klucze API, dane bramek SMS i payment).

### 3.2 Minimalne wymagania migracyjne
1. Eksport/import danych tylko dla wskazanego `tenant_id`.
2. Walidacja spojnosc po migracji: uzytkownicy, klienci, wizyty, magazyn, platnosci, raporty.
3. Plan cutover:
- freeze zapisu,
- finalny export,
- import,
- testy smoke,
- przelaczenie DNS.
4. Plan rollback z limitem czasu i zakresem utraty danych.

### 3.3 Wymagania operacyjne
1. Osobny monitoring, alerting i log retention per instancja.
2. Osobny harmonogram backup + okresowe testy odtworzeniowe.
3. Aktualizacje bezpieczenstwa i migracje DB musza byc wykonywane per instancja.

## 4. Zasady RODO (privacy by design)
Uwaga: to zasady techniczne, nie porada prawna.

### 4.1 Minimalizacja danych
1. Zbieramy tylko dane niezbedne do realizacji procesow salonowych.
2. Kazde nowe pole danych osobowych musi miec uzasadnienie biznesowe i okres retencji.
3. Zakaz przechowywania danych "na zapas".

### 4.2 Podstawowe zabezpieczenia
1. Dane w tranzycie: TLS.
2. Dane wrazliwe w bazie i backupach: szyfrowanie na poziomie dysku/volumenu oraz kontrola kluczy.
3. Hasla: tylko hash + salt (bez plaintext).
4. Sekrety: tylko przez manager sekretow / zmienne srodowiskowe, nigdy w repo.

### 4.3 Kontrola dostepu i audyt
1. RBAC + zasada najmniejszych uprawnien.
2. Dostep administracyjny tylko przez kontrolowany kanal (VPN + 2FA).
3. Logi audytowe operacji na danych osobowych (kto, co, kiedy, tenant).
4. Logi nie moga zawierac pelnych danych wrazliwych.

### 4.4 Retencja i usuwanie danych
1. Dla kazdej kategorii danych definiujemy okres retencji.
2. Proces usuwania/anonymizacji musi byc automatyzowalny i raportowalny.
3. Backupy musza miec polityke retencji zgodna z polityka danych.

### 4.5 Realizacja praw osoby, ktorej dane dotycza
1. Musimy umiec:
- wyszukac dane osoby,
- wyeksportowac dane,
- poprawic dane,
- usunac lub zanonimizowac dane (gdy podstawa prawna na to pozwala).
2. Operacje musza byc tenant-scoped i audytowalne.

### 4.6 Umowy i transfer danych
1. Kazdy zewnetrzny procesor danych (SMS, email, hosting, backup) wymaga rejestru i podstawy przetwarzania.
2. Dla transferu poza EOG wymagane sa odpowiednie zabezpieczenia formalne.

## 5. Definition of Done (architektura + RODO)
Nowa funkcja jest "done", gdy:
1. Jest tenant-safe i nie omija izolacji.
2. Jest zgodna z licencjonowaniem modulowym (API + UI).
3. Ma okreslone dane osobowe, retencje i zasady dostepu.
4. Ma testy dla sciezek uprawnien i izolacji tenantow.
5. Nie dodaje sekretow lub danych wrazliwych do logow.
