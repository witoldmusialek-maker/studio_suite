# Help głównego managera

## 1. Rola głównego managera
Jesteś właścicielem procesu w całej firmie.
Twoim celem nie jest klikanie pojedynczych wizyt, tylko utrzymanie poprawnego łańcucha danych:
cennik -> pakiety -> receptury -> wykonanie -> rozliczenie -> magazyn -> raport.
Jeśli którykolwiek element jest błędny, raport końcowy traci wartość.

## 2. Logika aplikacji w jednym zdaniu
Aplikacja działa poprawnie tylko wtedy, gdy każda usługa i pakiet mają poprawny czas, cenę oraz regułę zużycia materiału, a recepcja i zespół zapisują wykonanie zgodnie z rzeczywistością.

## 3. Pierwsza konfiguracja po uruchomieniu salonu
Kolejność jest obowiązkowa, bo kolejne moduły zależą od poprzednich.
1. Uzupełnij `Salony i zasoby`: salony, pracownicy, role, przypięcie kont logowania.
2. Uzupełnij `Farby i kolory`: aktywne produkty usługowe i sprzedażowe, rodziny, jednostki, ceny zakupu.
3. Uzupełnij `Cennik usług`: kody, nazwy, czasy trwania, ceny.
4. Uzupełnij `Pakiety (forfety)`: skład, cena końcowa, oznaczenie promocyjnych.
5. Uzupełnij `Receptury` dla usług materiałowych.
6. Zweryfikuj `Kalendarz`: czy godziny i dostępność pracowników są zgodne z grafikiem.
7. Wykonaj testową wizytę end-to-end i testowe rozliczenie.

## 4. Moduł Salony i zasoby
Za co odpowiada:
- kto pracuje, w jakim salonie, z jaką rolą operacyjną.

Co musisz ustawić:
1. Każdy aktywny pracownik ma rolę operacyjną:
   - Fryzjer,
   - Asystent,
   - Kosmetyczka/Manikiurzystka,
   - Recepcjonista,
   - Manager salonu.
2. Każde konto logowania jest przypięte do właściwej osoby.
3. Konto recepcji jest przypięte do jednego salonu.
4. Dla specjalistów ustawione są:
   - lista dozwolonych forfetów,
   - grafik pracy miesięczny.

### 4.1 Grafik miesięczny - model obowiązujący
1. Grafik planujemy i rozliczamy miesięcznie (nie tygodniowo).
2. Harmonogram można układać przez planner (drag and drop) i kopiowanie dni między datami.
3. Zapis „jako obowiązujący” publikuje plan jako źródło dostępności specjalistów.
4. Dostępność w kalendarzu i rezerwacji online musi wynikać z grafiku pracownika.

Najczęstszy błąd:
- konto działa, ale nie ma przypiętego pracownika lub salonu, więc użytkownik „nie widzi danych”.

## 5. Moduł Użytkownicy i role
Za co odpowiada:
- bezpieczeństwo i zakres dostępu.

Minimalne zasady:
1. Brak kont współdzielonych.
2. Każdy użytkownik ma tylko potrzebne uprawnienia.
3. Hasła i TOTP dla kont krytycznych.
4. Konta nieużywane wyłączaj, nie usuwaj na ślepo.

Konsekwencja błędu:
- nawet poprawne dane operacyjne stają się niewidoczne lub edytowalne przez nieuprawnione osoby.

## 6. Moduł Farby i kolory (podstawa receptur i magazynu)
Za co odpowiada:
- słownik produktów używany przez receptury, rozchody i stany magazynu.

Co musi być poprawne:
1. Rodzina produktu (np. SZAMPON, FARBA, OXYDANTY, MASKA).
2. Typ przeznaczenia:
   - produkt do usług,
   - produkt sprzedażowy,
   - pozostałe.
3. Jednostka i parametry dozowania (tam gdzie dotyczy).
4. Cena zakupu (do kalkulacji kosztu usługi i marży).
5. Status aktywności produktu.

Reguła:
- nieaktywne produkty zostawiamy historycznie, ale nie używamy ich do nowych receptur.

### 6.1 Jak dodać nowy produkt usługowy (krok po kroku)
1. Wejdź w `Farby i kolory`.
2. Wybierz salon.
3. Kliknij `Nowy produkt - usługa`.
4. Uzupełnij minimum:
   - Nazwa,
   - Marka,
   - Rodzina,
   - Cena zakupu,
   - Jednostka/parametry dozowania (jeśli produkt jest ważony lub dozowany),
   - Aktywny = TAK.
5. Zapisz.
6. Sprawdź, czy produkt pojawił się pod właściwą rodziną.

### 6.2 Jak dodać nowy produkt sprzedażowy (krok po kroku)
1. Kliknij `Nowy produkt - sprzedaż`.
2. Uzupełnij:
   - Nazwa,
   - Marka,
   - Rodzina sprzedażowa,
   - Cena sprzedaży,
   - Cena zakupu (dla marży),
   - Aktywny = TAK.
3. Zapisz.

### 6.3 Modal produktu - znaczenie pól
- `Kod produktu`: identyfikator legacy; dla istniejących rekordów traktuj jako techniczny.
- `Nazwa`: główna nazwa robocza produktu (widoczna na listach i w wyszukiwaniu).
- `Nazwa PL`: alternatywna nazwa opisowa.
- `Marka`: producent/linia (pomaga odróżnić podobne produkty).
- `FISK`: kod fiskalny (używany głównie dla sprzedaży detalicznej).
- `Rodzina`: najważniejsze pole dla receptur; to po nim filtruje się wybór materiału.
- `Poj.` / `Pojemność netto`: ilość netto produktu (ml/g/szt.).
- `Cena zak.`: koszt zakupu; kluczowy dla kalkulacji kosztu usługi.
- `Cena sprz.`: cena detaliczna dla sprzedaży klientowi.
- `Stan 100%`: docelowy poziom dla salonu (nie stan faktyczny).
- `Waga pełna` i `Waga pustego opakowania`: do liczenia zużycia produktów ważonych.
- `Doz w opakowaniu` / `ml/g na dozę`: parametry operacyjne do przeliczeń zużycia.
- `Aktywny`: czy produkt może być używany w nowych operacjach.

### 6.4 Jak ocenić, czy dane produktu są poprawne
Produkt jest gotowy do pracy, gdy:
1. ma poprawną rodzinę,
2. ma właściwą jednostkę,
3. ma cenę zakupu,
4. jest aktywny,
5. (dla chemii) ma komplet danych do doz/wag.

## 7. Moduł Cennik usług
Za co odpowiada:
- czas i wartość każdej usługi wykonywanej w salonie.

Co musi być ustawione na każdej usłudze:
1. Kod usługi.
2. Nazwa.
3. Czas trwania.
4. Cena.
5. Znacznik segmentu (Pani/Pan/Estetyka/Sprzedaż/Pomocnicza).

Ważne:
- usługa może nie mieć receptury tylko wtedy, gdy realnie nie zużywa materiału.

## 8. Moduł Pakiety (forfety)
Za co odpowiada:
- sprzedaż zestawów usług z łączną ceną.

Dobre praktyki:
1. Pakiet ma logiczny łączny czas.
2. Cena pakietu jest niższa od sumy usług, jeśli to promocja.
3. Pakiety promocyjne oznaczaj tak, aby były czytelne dla recepcji i samorezerwacji.
4. Przypisuj pakiety do konkretnych specjalistów tylko wtedy, gdy faktycznie mają je wykonywać.

### 8.9 Rezerwacja publiczna - reguła przypisania forfetów
1. W rezerwacji online klient widzi tylko forfety przypisane do wybranego specjalisty.
2. Brak przypisań = brak forfetów dla danego specjalisty.
3. Zmiana przypisań działa bezpośrednio na ofertę publiczną, więc traktuj ją jako zmianę produkcyjną.

### 8.8 Modal dodawania/edycji pakietu - jak czytać pola
- `Kod pakietu`: unikalny identyfikator pakietu (np. kod promocji).
- `Nazwa pakietu`: nazwa widoczna dla recepcji i klienta.
- `Cena pakietu`: cena końcowa płacona przez klienta.
- `Pozycje pakietu`: lista usług wchodzących do pakietu.
- `Cena pozycji w pakiecie` (jeśli edytowalna): techniczny podział ceny pakietu na usługi składowe.
- `Aktywny`: czy pakiet ma być możliwy do sprzedaży/rezerwacji.

Jak ustawić poprawnie:
1. Najpierw wybierz usługi składowe.
2. Sprawdź łączny czas pakietu.
3. Ustal cenę końcową.
4. Oznacz pakiet jako aktywny dopiero po teście na jednej próbnej rezerwacji.

## 9. Moduł Receptury (najważniejszy dla kosztu i magazynu)
Za co odpowiada:
- jak system liczy zużycie materiału przy wykonaniu usług.

Co ustawić w recepturze:
1. Pozycję główną (rodzina lub konkretny produkt).
2. Tryb ilości:
   - Dokładna (jedna wartość),
   - Zakres (min, domyślna, max).
3. Jednostkę operacyjną (g, ml, szt., pcs).
4. Czy pozycja jest wymagana.
5. Dodatkowe zasoby, jeśli są potrzebne.

Zasada biznesowa:
- lepiej mieć zakres i potem wpisać zużycie rzeczywiste niż udawać dokładność.

Konsekwencje błędnej receptury:
1. błędny koszt usługi,
2. błędne stany magazynowe,
3. fałszywe raporty efektywności pracowników.

### 9.1 Jak utworzyć recepturę usługi (procedura obowiązkowa)
1. Wejdź w `Cennik usług`.
2. Znajdź usługę i kliknij `Receptura`.
3. Dodaj pozycję główną:
   - wybierz `Rodzinę produktu`,
   - opcjonalnie wskaż `Konkretny produkt` (jeśli ma być sztywno narzucony),
   - ustaw `Tryb ilości` i normę.
4. Oznacz `Pozycja wymagana`, jeśli usługa nie może być wykonana bez tego zasobu.
5. Dodaj kolejne pozycje (np. oksydant, maska, jednorazówki).
6. Zapisz każdą pozycję.
7. Przetestuj usługę na próbnej wizycie i sprawdź, czy rozchód jest logiczny.

### 9.2 Modal receptury - tabela pozycji (górna część)
- `Typ`: `Główna` lub `Dodatkowy zasób`.
- `Rodzina`: rodzina produktu przypisana do pozycji.
- `Domyślny produkt`: produkt podpowiadany lub wymuszony.
- `Poz.`: kolejność pozycji (istotna dla czytelności i eksportu).
- `Tryb`: sposób liczenia ilości (`EXACT`/`RANGE` lub odpowiedniki PL).
- `Min`, `Domyślna`, `Max`: wartości normy.
- `JM`: jednostka miary pozycji (g/ml/szt./pcs).
- `Akcje`: edycja, duplikacja, usunięcie pozycji.

### 9.3 Modal receptury - formularz (dolna część) i znaczenie pól
- `Rodzina produktu`: filtr i główne źródło do wyboru materiału podczas rozliczenia.
- `Konkretny produkt (opcjonalnie)`: ustaw, gdy ma być używany jeden, konkretny produkt.
- `Pozycja`: numer kolejności na liście.
- `Tryb ilości`:
  - `Dokładna`: jedna wartość zużycia,
  - `Zakres`: min/domyślna/max dla różnych przypadków.
- `Sposób rozliczania`: kiedy norma nalicza się w usłudze (na każdej usłudze / per przypadek).
- `Ilość`: wartość normy przy trybie dokładnym.
- `Min/Domyślna/Max`: wartości normy przy trybie zakresowym.
- `Jednostka operacyjna`: jednostka wpisu zużycia przez personel.
- `Pozycja wymagana`: blokuje poprawne rozliczenie bez wskazania zużycia.
- `Dodatkowy zasób`: oznacza pozycję pomocniczą (np. jednorazówki).
- `Notatka`: opis dla personelu, kiedy i jak użyć pozycji.

### 9.4 Kiedy wybierać rodzinę, a kiedy konkretny produkt
Wybierz samą `Rodzinę`, gdy:
1. produkt może się zmieniać zależnie od decyzji fryzjera,
2. liczy się typ zasobu, nie marka.

Wybierz `Konkretny produkt`, gdy:
1. procedura wymaga jednego określonego preparatu,
2. chcesz pełną standaryzację i brak zamienników.

### 9.5 Jak ustawiać ilość (praktyka)
1. Dla usług przewidywalnych: `Dokładna`.
2. Dla usług zależnych od długości/gęstości włosów: `Zakres`.
3. `Domyślna` powinna odpowiadać najczęstszemu przypadkowi.
4. `Max` ustaw tak, aby pokryć realny górny przypadek bez nadużyć.

### 9.6 Co oznacza „pozycja wymagana” w praktyce
Jeśli pozycja jest wymagana:
1. personel musi podać zużycie, żeby poprawnie domknąć rozliczenie,
2. brak wpisu = ryzyko rozjazdu kosztu i magazynu.

Jeśli pozycja jest opcjonalna:
1. używaj tylko dla zasobów faktycznie nieregularnych,
2. nie oznaczaj głównych składników chemii jako opcjonalnych.

### 9.7 Kontrola jakości receptury po zapisaniu
Po każdej zmianie wykonaj test:
1. zrób testową wizytę z tą usługą,
2. przejdź przez rozliczenie,
3. sprawdź czy system wymaga właściwych pozycji,
4. sprawdź czy rozchód i koszt wyglądają logicznie.

### 9.8 Najczęstsze błędy managera przy recepturach
1. Brak pozycji wymaganej dla głównego składnika.
2. Zła jednostka (np. szt. zamiast g).
3. Zbyt niski `Max`, który nie pokrywa realnych przypadków.
4. Przypisanie rodziny sprzedażowej zamiast usługowej.
5. Zmiana receptury bez testu na wizycie kontrolnej.

### 9.9 Skutek biznesowy zmian receptury
Każda zmiana receptury wpływa jednocześnie na:
1. koszt jednostkowy usługi,
2. marżę,
3. obciążenie magazynu,
4. wyniki rozliczania pracowników.
Dlatego recepturę zmieniaj celowo, małymi krokami i z testem.

## 10. Rezerwacje online, OTP i status pending
1. Rezerwacja publiczna po poprawnym OTP zapisuje się jako `pending`.
2. `Pending` blokuje slot i czeka na decyzję recepcji/managera.
3. Akceptacja/odrzucenie odbywa się w `Kalendarz wizyt -> Szczegóły wizyty`:
   - `Potwierdz` -> status `confirmed` + SMS potwierdzający,
   - `Odrzuc` -> status `cancelled` + SMS odrzucający.
4. Kod OTP jest powiązany z konkretnym żądaniem (slot/specjalista/oferta) i ma krótki TTL.
5. Przy błędach klient powinien wygenerować nowy kod i użyć tylko ostatniego SMS.

## 11. Powiadamianie o nowych rezerwacjach
1. Panel pokazuje popup dla nowych wizyt `pending` (globalnie w aplikacji).
2. Popup jest sygnałem operacyjnym, aby natychmiast przejść do kalendarza i podjąć decyzję.
3. Brak reakcji na `pending` powoduje sztuczne blokowanie terminów i spadek konwersji.

## 10. Kalendarz i obsługa wizyt
Główny manager zwykle nie dodaje wizyt, ale kontroluje proces.

Co sprawdzać:
1. czy wizyty mają poprawne statusy,
2. czy brak konfliktów czasowych,
3. czy wizyty wykonane są domknięte rozliczeniem,
4. czy anulacje i nieobecności (no-show) są oznaczane.

Reguła:
- status musi odzwierciedlać rzeczywistość, bo inaczej KPI dnia są błędne.

## 11. Rozliczenie wizyty
Co musi być wpisane:
1. lista wykonanych usług,
2. wykonawca każdej pozycji,
3. ewentualna sprzedaż detaliczna,
4. formy płatności (gotówka/karta/voucher itd.),
5. finalny status płatności.

Jeśli wizyta była pakietem:
- pakiet powinien rozwinąć się na usługi składowe, aby poprawnie rozliczyć pracę i koszty.

## 12. Magazyn i remanent
Podział odpowiedzialności:
1. Recepcja/manager salonu: wykonuje liczenie i ważenie (remanent).
2. Główny manager: analizuje różnice, zatwierdza decyzje operacyjne.

Ważne:
- osoba wpisująca remanent nie powinna znać stanu systemowego (żeby nie „dopasowywać” wyniku).
- stan 100 procent to poziom docelowy dla salonu, a nie stan rzeczywisty.

## 13. Codzienna rutyna głównego managera
Kolejność kontroli (15-30 minut dziennie):
1. Dashboard: wykonane, anulowane, no-show.
2. Kalendarz: wizyty bez domknięcia.
3. Rozliczenia: brakujące płatności i odchylenia.
4. Magazyn: istotne różnice i krytyczne braki.
5. Zespół: grafiki i przypisania.

## 14. Tygodniowa rutyna głównego managera
1. Przegląd cen i czasów usług.
2. Przegląd pakietów promocyjnych.
3. Audyt receptur usług materiałowych.
4. Przegląd jakości danych klientów i pracowników.
5. Kontrola uprawnień i aktywnych kont.

## 15. Miesięczny audyt jakości danych
Sprawdź i popraw:
1. usługi bez segmentu,
2. usługi materiałowe bez receptury,
3. receptury bez wymaganych pozycji,
4. produkty bez rodziny lub z niepoprawną jednostką,
5. pracowników bez roli lub bez salonu.

## 16. Samorezerwacja klienta (public booking)
Cel:
- pozyskanie rezerwacji bez obciążania recepcji.

Przepływ:
1. Klient wybiera salon.
2. Wybiera specjalistę i wolny slot.
3. Wybiera forfet przypisany do tego specjalisty.
4. Potwierdza numer telefonu kodem OTP.
5. Rezerwacja trafia do kalendarza salonu.

Link testowy:
- `/public/client-booking`

Co kontrolować:
1. czy wyświetlają się tylko właściwi specjaliści,
2. czy dostępne są właściwe forfety,
3. czy czas pakietu poprawnie blokuje sloty.

## 17. Najczęstsze awarie i szybka diagnoza
Przypadek: użytkownik nie widzi danych.
Sprawdź:
1. rolę konta logowania,
2. przypięcie do pracownika,
3. przypięcie pracownika do salonu,
4. aktywność konta i pracownika.

Przypadek: magazyn się rozjeżdża.
Sprawdź:
1. receptury usług materiałowych,
2. czy wpisano zużycie rzeczywiste przy rozliczeniu,
3. czy remanent wykonano poprawnie.

Przypadek: błędna marża usługi.
Sprawdź:
1. cenę usługi,
2. cenę zakupu produktów,
3. normy w recepturze.

## 18. Zasada aktualizacji tej dokumentacji
Po każdej zmianie workflow aplikacji aktualizujesz ten dokument w tym samym wdrożeniu.
Brak aktualizacji pomocy oznacza ryzyko błędnej pracy operacyjnej.
