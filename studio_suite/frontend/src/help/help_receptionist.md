# Help obsługi recepcji

## Cel
Szybka i poprawna obsługa klienta od wejścia do salonu do zakończenia płatności.

## Standardowy przebieg pracy
1. Sprawdź dostępność specjalistów na dziś (`Dashboard` + `Kalendarz wizyt`).
2. Najpierw obsłuż rezerwacje oczekujące (`pending`) z kanału online.
2. Dla klienta walk-in:
   - załóż wizytę z minimalnymi danymi,
   - wybierz specjalistę i najbliższy wolny slot.
3. Po wykonaniu usługi:
   - uzupełnij wykonane pozycje (usługa lub forfet),
   - przypisz wykonującego do każdej pozycji,
   - uzupełnij produkty sprzedażowe (jeśli były).
4. Zamknij wizytę płatnością (gotówka/karta/voucher).
5. Jeśli klient nie przyszedł:
   - oznacz wizytę jako `Nie pojawił się`.
   - jeśli odwołał wcześniej: `Anulowana`.

## Konsekwencje działań recepcji
1. Utworzenie wizyty:
   - zajmuje slot w kalendarzu i blokuje ten czas dla specjalisty,
   - błąd w godzinie lub specjaliście powoduje konflikt obłożenia.
2. Zmiana terminu:
   - przesuwa obłożenie dnia i wpływa na „wolne okna” innych klientów.
3. Oznaczenie `Wykonana`:
   - uruchamia proces rozliczenia i wpływa na wyniki dzienne.
4. Oznaczenie `Anulowana`:
   - zwalnia slot; w raportach obniża skuteczność realizacji.
5. Oznaczenie `Nie pojawił się`:
   - slot był zablokowany bez przychodu; wpływa na KPI frekwencji.
6. Dodanie linii wykonania:
   - buduje historię klienta, statystyki usług i wyniki pracowników.
   - brak linii = niepełna historia i błędne raporty.
7. Rozliczenie płatności:
   - zamyka wizytę finansowo.
   - błędna forma/kwota = rozjazd raportów kasowych i dziennych.

## Rezerwacje online (OTP + status pending)
1. Rezerwacja z publicznej strony po OTP zapisuje się jako `pending` (oczekuje na potwierdzenie).
2. `Pending` blokuje slot w kalendarzu, ale wymaga decyzji recepcji/managera.
3. W `Kalendarz wizyt -> Szczegóły wizyty` użyj:
   - `Potwierdz` -> status `confirmed` i SMS potwierdzający dla klienta,
   - `Odrzuc` -> status `cancelled` i SMS odrzucający.
4. Jeśli klient zgłasza błąd OTP:
   - poproś o ponowne `Wyślij kod OTP`,
   - używaj tylko najnowszego kodu (starsze wyzwania OTP nie przejdą).

## Popup o nowych rezerwacjach
1. System pokazuje popup, gdy pojawi się nowa wizyta `pending`.
2. Z popupu kliknij `Otworz kalendarz`, aby od razu przejść do obsługi.
3. Jeśli popup zamkniesz, slot dalej jest widoczny jako `pending` w kalendarzu.

## Remanent (tryb recepcji)
1. W remanencie wpisujesz wynik liczenia/ważenia, bez podglądu stanu systemowego.
2. Pracuj po liście produktów:
   - produkt na sztuki: wpisz liczbę sztuk,
   - produkt na wagę/dozy: wpisz wagę/ilość wg podpowiedzi.
3. Pozycje zapisuj na bieżąco i poprawiaj w tabeli pomocniczej przed zatwierdzeniem.

## Najczęstsze błędy
- Zły salon: zawsze sprawdź aktywny salon konta.
- Zła godzina wizyty: zapisuj tylko sloty zgodne z kalendarzem.
- Brak rozliczenia: wizyta `wykonana` musi mieć uzupełnioną płatność.
- Brak wykonawcy przy linii usługi: rozliczenie pracownika i marży będzie błędne.
- Pomylenie `Anulowana` i `Nie pojawił się`: fałszuje wskaźniki frekwencji.

## Zasada aktualizacji dokumentu
Po każdej zmianie workflow recepcji ta instrukcja musi być zaktualizowana w tym samym wdrożeniu.
