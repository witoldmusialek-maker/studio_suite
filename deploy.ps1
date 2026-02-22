# Skrypt deploy na maszynę dev1
# Użycie: .\deploy.ps1

$DEV_HOST = "192.168.200.116"
$DEV_USER = "witold"
$DEV_PATH = "/home/witold/digital_signage"  # Zmień jeśli ścieżka jest inna
$LOCAL_PATH = "c:\Users\Wit\projekty\cline\projekt1\digital_signage"

Write-Host "=== Deploy Digital Signage na dev1 ===" -ForegroundColor Cyan
Write-Host ""

# 1. Sprawdzenie połączenia
Write-Host "1. Sprawdzanie połączenia SSH..." -ForegroundColor Yellow
ssh -o ConnectTimeout=5 "$DEV_USER@$DEV_HOST" "echo 'Połączenie OK'"
if ($LASTEXITCODE -ne 0) {
    Write-Host "BŁĄD: Nie można połączyć się z serwerem dev1" -ForegroundColor Red
    Write-Host "Sprawdź hasło i połączenie sieciowe" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Połączenie działa" -ForegroundColor Green
Write-Host ""

# 2. Sprawdzenie czy istnieje katalog projektu na dev1
Write-Host "2. Sprawdzanie struktury projektu na dev1..." -ForegroundColor Yellow
ssh "$DEV_USER@$DEV_HOST" "ls -la $DEV_PATH/backend/app/api/v1/content.py 2>/dev/null"
if ($LASTEXITCODE -ne 0) {
    Write-Host "BŁĄD: Nie znaleziono projektu w $DEV_PATH" -ForegroundColor Red
    Write-Host "Podaj poprawną ścieżkę i edytuj zmienną DEV_PATH w tym skrypcie" -ForegroundColor Yellow
    exit 1
}
Write-Host "✓ Projekt znaleziony" -ForegroundColor Green
Write-Host ""

# 3. Wysłanie poprawionego pliku
Write-Host "3. Wysyłanie poprawionego pliku content.py..." -ForegroundColor Yellow
scp "$LOCAL_PATH\backend\app\api\v1\content.py" "$DEV_USER@${DEV_HOST}:$DEV_PATH/backend/app/api/v1/content.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "BŁĄD: Nie można wysłać pliku" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Plik wysłany" -ForegroundColor Green
Write-Host ""

# 4. Restart aplikacji
Write-Host "4. Sprawdzanie metody uruchomienia aplikacji..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Wykrywanie metody uruchomienia:" -ForegroundColor Cyan

# Sprawdź docker-compose
ssh "$DEV_USER@$DEV_HOST" "cd $DEV_PATH && docker-compose ps 2>/dev/null | grep -q 'Up'" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Wykryto Docker Compose" -ForegroundColor Green
    Write-Host "Restartuję backend przez docker-compose..." -ForegroundColor Yellow
    ssh "$DEV_USER@$DEV_HOST" "cd $DEV_PATH && docker-compose restart backend"
    Write-Host "✓ Backend zrestartowany" -ForegroundColor Green
} else {
    # Sprawdź systemd
    ssh "$DEV_USER@$DEV_HOST" "systemctl is-active --quiet digital-signage-backend 2>/dev/null"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Wykryto systemd service" -ForegroundColor Green
        Write-Host "Restartuję backend przez systemctl..." -ForegroundColor Yellow
        ssh "$DEV_USER@$DEV_HOST" "sudo systemctl restart digital-signage-backend"
        Write-Host "✓ Backend zrestartowany" -ForegroundColor Green
    } else {
        # Sprawdź proces uvicorn
        ssh "$DEV_USER@$DEV_HOST" "pgrep -f 'uvicorn.*app.main:app' >/dev/null 2>&1"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Wykryto proces uvicorn" -ForegroundColor Green
            Write-Host "UWAGA: Musisz ręcznie zrestartować backend!" -ForegroundColor Yellow
            Write-Host "Wykonaj na dev1:" -ForegroundColor Cyan
            Write-Host "  pkill -f uvicorn" -ForegroundColor White
            Write-Host "  cd $DEV_PATH/backend && uvicorn app.main:app --reload &" -ForegroundColor White
        } else {
            Write-Host "⚠ Nie wykryto metody uruchomienia" -ForegroundColor Yellow
            Write-Host "Musisz ręcznie zrestartować backend na dev1" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "=== Deploy zakończony ===" -ForegroundColor Cyan
Write-Host "Sprawdź aplikację: http://$DEV_HOST:8000/docs" -ForegroundColor Green
