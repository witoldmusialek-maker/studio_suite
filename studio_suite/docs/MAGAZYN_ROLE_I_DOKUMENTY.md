# Magazyn - role i dokumenty (model operacyjny)

## Cel
Ujednolicony obieg dokumentow magazynowych:
- recepcjonista liczy i wpisuje remanent,
- manager/admin weryfikuje i zatwierdza,
- system generuje uzupelnienia na podstawie `stan_100% - stan_rzeczywisty`.

## Zakres odpowiedzialnosci

### Recepcjonista
- wykonuje remanent (liczenie sztuk / wazenie),
- zapisuje dokument remanentu w statusie `PLANNED`,
- nie zatwierdza dokumentow magazynowych,
- nie generuje zamowien.

### Manager salonu
- weryfikuje remanent i zatwierdza dokumenty (`PLANNED -> POSTED`),
- generuje propozycje uzupelnienia (replenishment),
- prowadzi przyjecie dostawy (PZ) i rozchod wewnetrzny (RW/WZ).

### Admin / glowny manager
- ma uprawnienia managera dla wszystkich salonow,
- nadzoruje roznice remanentowe i audyt.

## Dokumenty i statusy

### 1) Remanent (inwentaryzacja)
- technicznie: `inventory_issues` + `inventory_issue_lines`
- status:
  - `PLANNED` - policzone, czeka na weryfikacje,
  - `POSTED` - zatwierdzone i przepisane na stany.

### 2) Korekta reczna (delta)
- technicznie: `inventory_issues` (`remarks` = korekta reczna),
- status:
  - `PLANNED` - przygotowana do zatwierdzenia,
  - `POSTED` - zatwierdzona.

### 3) Rozchod uslugowy
- technicznie: `inventory_issues` powiazane z wizyta/usluga,
- status:
  - `PLANNED` - szkic (edycja),
  - `POSTED` - zatwierdzony rozchod.

### 4) Uzupelnienie (zamowienie)
- technicznie obecnie: `replenishment_suggestions`
- znaczenie:
  - `OPEN` - brak do uzupelnienia,
  - `CLOSED` - uzupelnione/rozliczone.

Docelowo (kolejny etap) rekomendowane osobne dokumenty:
- `PO` (zamowienie do dostawcy),
- `PZ` (przyjecie dostawy),
- `MM/RW/WZ` (wydania i przesuniecia).

## Aktualne zasady systemowe (wdrozone)

1. Remanent zapisany przez recepcjoniste:
- tworzy dokument `PLANNED`,
- nie zmienia stanu od razu.

2. Zatwierdzenie dokumentu:
- tylko `admin/manager`,
- przy zatwierdzeniu stany sa aktualizowane.

3. Generowanie sugestii uzupelnienia:
- tylko `admin/manager`.

4. Lokalizacja magazynowa:
- domyslnie jedna lokalizacja techniczna na salon (`SALON_GLOWNY`),
- jesli nie istnieje, system tworzy ja automatycznie.

