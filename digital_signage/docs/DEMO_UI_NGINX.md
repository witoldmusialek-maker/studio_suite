# Demo UI przez Nginx

Serwis wystawia statyczne strony demo z `frontend/public` na porcie `8088`.

## Start

```powershell
docker compose -f digital_signage/docker-compose.demo-ui.yml up -d
```

## Stop

```powershell
docker compose -f digital_signage/docker-compose.demo-ui.yml down
```

## URL-e

- `http://localhost:8088/demo.html`
- `http://localhost:8088/demo-playlisty.html`
- `http://localhost:8088/demo-typy-dnia.html`
- `http://localhost:8088/demo-kalendarz.html`
- `http://localhost:8088/demo-sterowanie.html`

## Wystawienie na zewnątrz

Wystaw publicznie port hosta `8088` (NAT/reverse proxy/firewall), np.:

- reverse proxy: `https://twoja-domena/` -> `http://host:8088/`
- lub bezpośrednio `http://twoj-host:8088/demo.html`

