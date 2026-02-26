# TESTING - Studio Suite v1

## Recommended path (Windows + Docker)

```powershell
cd studio_suite
docker compose up -d --build
```

Create admin once:

```powershell
docker compose exec -T backend python scripts/create_admin.py admin password123
```

Run smoke test:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_test.ps1
```

## Manual functional checklist

1. Login
- Open `http://localhost:3000`
- Login as `admin / password123`
- Verify dashboard loads

2. Displays
- Add a display from `Displays` page
- Edit name/orientation/resolution
- Delete display

3. Content
- Upload PNG/JPG in `Content`
- Verify item appears
- Verify thumbnail appears after processing
- Delete content

4. Heartbeat/status
- Register display through API (`/displays/register`)
- Send heartbeat (`/displays/{id}/heartbeat`)
- Verify `status=online` and `last_seen` updates

5. Schedules
- Create schedule active for current time
- Verify `/schedules/display/{id}/current` returns assigned content

6. Groups
- Create `horizontal` group
- Add first display (must work)
- Add second display (must work)

7. Reports
- Check `daily`, `weekly`, `offline`
- Check `export-csv` endpoints return CSV

8. Bells
- Upload sound
- Create bell schedule for current minute
- Check `/bells/display/{id}/play-command`
- Call `/bells/mark-played`
- Verify history in `/bells/{id}/history`

## API references

- Swagger: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

## Stop environment

```powershell
cd studio_suite
docker compose down
```

