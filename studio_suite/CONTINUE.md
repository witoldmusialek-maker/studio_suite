CONTINUE (handoff 2026-02-26)

Zakres i separacja projektow
- NIE ruszac: `dev.witold.ovh` (digital signage / projekt1).
- Pracujemy tylko na: `dev2.witold.ovh` (Studio Suite / projekt2).
- Repo lokalne: `C:\Users\Wit\projekty\cline\projekt2\studio_suite`
- Repo na serwerze: `~/projects/projekt2_repo/studio_suite`

Aktualna wersja
- Backend + frontend: `v1.0.0-beta.2026-02-26.09`
- Commit wersji: `01ea8de`

Najwazniejsze zmiany z tej sesji
- Przebudowana tabela produktow pod import 1:1 z ODS.
- Jedna wspolna baza produktow (ta sama tabela), bez separacji danych per salon.
- W UI pokazujemy jedna kolumne magazynowa zalezna od salonu:
  - salon 05 -> `MX03`
  - salon 12 -> `MX04`
  - salon 07 -> `MX07`
- Dodane filtry do wszystkich kolumn w widoku tabeli produktow.
- `ID_P` jest kodem relacyjnym produktu (`legacy_code`).
- Dodane/obslugiwane pola: `NAZWA1`, `NAZWAPL`, `FISK`, `POJ`, `CENAKATNET`, `CENASPBRT`, `CENA_ZAK`, `S_U` i pozostale kolumny 1:1 (z pominiêciami uzgodnionymi).

Krytyczna poprawka importera
- Commit: `bdcdbd4`
- Problem: parser ODS czytal tylko `text:p`, a czesc liczb byla w `office:value`.
- Skutek: ceny byly puste mimo poprawnych wartosci w pliku.
- Naprawa: odczyt `office:value` / `office:string-value`.

Stan danych po ostatniej naprawie
- Import wykonano bezposrednio na `dev1` (zdalnie) z `--replace-all`.
- Biezacy wynik na dev2:
  - `legacy_product_catalog_items`: `2832`
  - zakres kodow: `10003 ... DOPISAÆ`
  - testowe rekordy (17056/17057/20001/20002/20007) maja poprawne ceny.

Wazne operacyjnie
- Sam deploy NIE uruchamia importu ODS.
- Po zmianach importera lub nowej paczce danych trzeba recznie uruchomic import na serwerze.
- Zdarzyl sie problem `no space left on device` na dev1 podczas deploy; pomoglo czyszczenie Docker cache.

Komendy referencyjne (dev1)
- Deploy:
  - `powershell -ExecutionPolicy Bypass -File scripts\\deploy-dev2.ps1`
- Czyszczenie miejsca (gdy brak miejsca):
  - `ssh dev1 "docker builder prune -af && docker image prune -af"`
- Import ODS (na serwerze):
  - `ssh dev1 --% "cd ~/projects/projekt2_repo/studio_suite && docker cp LUTYbaza20260224.ods studio_suite-backend-1:/tmp/LUTYbaza20260224.ods && docker exec studio_suite-backend-1 python scripts/import_products_ods_for_salon.py --input-file /tmp/LUTYbaza20260224.ods --salon-code 12 --salon-name Krasiñskiego --replace-all"`
- Szybka walidacja wersji:
  - `https://dev2.witold.ovh/health`

Zalecenie na kolejna sesje
- Pracowac bezposrednio na `dev1` (build/import/weryfikacja), z lokalnym repo jako backup.
- To minimalizuje rozjazdy miedzy lokalnym Docker a rzeczywistym stanem `dev2`.
