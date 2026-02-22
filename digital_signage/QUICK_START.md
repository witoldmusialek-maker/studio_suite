# Quick Start - Digital Signage

## Windows + Docker (recommended)

Start environment:

```powershell
cd digital_signage
docker compose up -d --build
```

Services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger: http://localhost:8000/docs

Create admin user:

```powershell
cd digital_signage
docker compose exec -T backend python scripts/create_admin.py admin password123
```

Login:
- username: `admin`
- password: `password123`

## Optional: server bell playback (T620 / radiowezel)

Set in `digital_signage/backend/.env`:

```env
BELL_SERVER_PLAYBACK_ENABLED=True
BELL_CLIENT_PLAYBACK_ENABLED=True
# Linux example:
# BELL_SERVER_PLAYER_CMD=ffplay -nodisp -autoexit "{file_path}"
```

Restart services:

```powershell
cd digital_signage
docker compose restart backend celery_worker celery_beat
```

## Optional: install radio client on T620

In `digital_signage/client`:

```powershell
cd digital_signage\client
copy radio_config.example.py radio_config.py
```

Edit `radio_config.py` (`SERVER_URL`, `MAC_ADDRESS`, `DISPLAY_NAME`) and run:

```powershell
python radio_client.py
```

Run smoke test:

```powershell
cd digital_signage
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_test.ps1
```

Stop environment:

```powershell
cd digital_signage
docker compose down
```

## Optional: recreate clean state

```powershell
cd digital_signage
docker compose down -v --remove-orphans
docker compose up -d --build
```
