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
- Frontend public: http://localhost:8084
- Backend public API: http://localhost:8004/api/v1

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

Porzadki lokalnego cache Android:

```powershell
Remove-Item -Recurse -Force .\android\sms_bridge\.gradle, .\android\sms_bridge\app\build
```

Zatrzymanie:

```powershell
cd studio_suite
docker compose down
```
