# TESTING - Studio Suite

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
- Open `http://localhost:8082`
- Login as `admin / password123`
- Verify dashboard loads

2. Salons and staff
- Open `Resources`
- Add/edit/delete salon
- Add/edit/delete staff member

3. Legacy catalog
- Open `Services` and verify CRUD for service
- Open `Bundles` and verify add/remove bundle item
- Open `Colors` and verify product list loads

4. Reports
- Open `Reports`
- Change date range and verify tables load

## API references

- Swagger: `http://localhost:8003/docs`
- Health: `http://localhost:8003/health`
- Public app: `http://localhost:8084`
- Public API docs: `http://localhost:8004/docs`

## Stop environment

```powershell
cd studio_suite
docker compose down
```
