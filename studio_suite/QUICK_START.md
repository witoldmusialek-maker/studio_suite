# Quick Start - Studio Suite

## Docker (recommended)

```powershell
cd studio_suite
docker compose up -d --build
```

Serwisy:
- Frontend: http://localhost:8082
- Backend API: http://localhost:8003/api/v1
- Swagger: http://localhost:8003/docs

Utworzenie admina:

```powershell
cd studio_suite
docker compose exec -T backend python scripts/create_admin.py admin password123
```

Test smoke:

```powershell
cd studio_suite
powershell -ExecutionPolicy Bypass -File .\scripts\smoke_test.ps1
```

Zatrzymanie:

```powershell
cd studio_suite
docker compose down
```
