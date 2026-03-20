# Help managera salonu

## Zakres odpowiedzialności
- Operacyjne działanie salonu przypisanego do konta.
- Nadzór nad kalendarzem, pracownikami, cennikami i stanami.
- Weryfikacja poprawności remanentu i dokumentów magazynowych.

## Codzienny checklist
1. `Dashboard`: obłożenie dnia, wizyty wykonane/odwołane, luki.
2. `Kalendarz`: konflikty terminów i nieobsadzone sloty.
3. `Cennik usług` / `Pakiety`: ceny i poprawność receptur.
4. `Farby i kolory`: aktywność produktów i rodziny do receptur.
5. `Magazyn`: stany operacyjne, dokumenty przyjęć/wydań.

## Zarządzanie zespołem
1. `Salony i zasoby`:
   - przypisania salonów,
   - przypisania forfetów do specjalistów,
   - grafiki miesięczne pracowników (z możliwością kopiowania dni między datami).
2. Konta logowania przypinaj tylko do realnych pracowników.

## Rezerwacje online i akceptacja
1. Rezerwacje z kanału publicznego zapisują się jako `pending`.
2. `Pending` zajmuje termin, ale wymaga decyzji salonu.
3. W `Kalendarz wizyt -> Szczegóły wizyty`:
   - `Potwierdz` zmienia na `confirmed` i wysyła klientowi SMS potwierdzający,
   - `Odrzuc` zmienia na `cancelled` i wysyła klientowi SMS odrzucający.
4. W panelu działa popup o nowych wizytach `pending` z szybkim przejściem do kalendarza.

## Publiczna rezerwacja - reguły forfetów i OTP
1. Klient wybiera termin u specjalisty, a potem widzi tylko forfety przypisane do tego specjalisty.
2. Kod OTP jest ważny krótko i jest powiązany z konkretnym żądaniem (slot + specjalista + oferta).
3. Przy błędach klienta zawsze zlecaj ponowne wygenerowanie kodu i użycie najnowszego SMS.

## Polityka jakości danych
- Każda usługa, która zużywa zasób, musi mieć recepturę.
- Produkty aktywne i nieaktywne muszą być jednoznacznie oznaczone.
- Zmiany cen i receptur wykonuj kontrolowanie (bez masowych przypadkowych edycji).

## Zasada aktualizacji dokumentu
Po każdej zmianie procesu managera salonu aktualizuj tę instrukcję w tym samym release.
