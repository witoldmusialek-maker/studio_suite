# Skrypt deploy na maszynÄ™ dev1
# UĹĽycie: .\deploy.ps1

$DEV_HOST = "192.168.200.116"
$DEV_USER = "witold"
$DEV_PATH = "/home/witold/projects/studio_suite_repo/studio_suite"  # ZmieĹ„ jeĹ›li Ĺ›cieĹĽka jest inna
$LOCAL_PATH = "c:\Users\Wit\projekty\cline\projekt2\studio_suite"

Write-Host "=== Deploy Studio Suite na dev1 ===" -ForegroundColor Cyan
Write-Host ""

# 1. Sprawdzenie poĹ‚Ä…czenia
Write-Host "1. Sprawdzanie poĹ‚Ä…czenia SSH..." -ForegroundColor Yellow
ssh -o ConnectTimeout=5 "$DEV_USER@$DEV_HOST" "echo 'PoĹ‚Ä…czenie OK'"
if ($LASTEXITCODE -ne 0) {
    Write-Host "BĹÄ„D: Nie moĹĽna poĹ‚Ä…czyÄ‡ siÄ™ z serwerem dev1" -ForegroundColor Red
    Write-Host "SprawdĹş hasĹ‚o i poĹ‚Ä…czenie sieciowe" -ForegroundColor Red
    exit 1
}
Write-Host "âś“ PoĹ‚Ä…czenie dziaĹ‚a" -ForegroundColor Green
Write-Host ""

# 2. Sprawdzenie czy istnieje katalog projektu na dev1
Write-Host "2. Sprawdzanie struktury projektu na dev1..." -ForegroundColor Yellow
ssh "$DEV_USER@$DEV_HOST" "ls -la $DEV_PATH/backend/app/api/v1/content.py 2>/dev/null"
if ($LASTEXITCODE -ne 0) {
    Write-Host "BĹÄ„D: Nie znaleziono projektu w $DEV_PATH" -ForegroundColor Red
    Write-Host "Podaj poprawnÄ… Ĺ›cieĹĽkÄ™ i edytuj zmiennÄ… DEV_PATH w tym skrypcie" -ForegroundColor Yellow
    exit 1
}
Write-Host "âś“ Projekt znaleziony" -ForegroundColor Green
Write-Host ""

# 3. WysĹ‚anie poprawionego pliku
Write-Host "3. WysyĹ‚anie poprawionego pliku content.py..." -ForegroundColor Yellow
scp "$LOCAL_PATH\backend\app\api\v1\content.py" "$DEV_USER@${DEV_HOST}:$DEV_PATH/backend/app/api/v1/content.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "BĹÄ„D: Nie moĹĽna wysĹ‚aÄ‡ pliku" -ForegroundColor Red
    exit 1
}
Write-Host "âś“ Plik wysĹ‚any" -ForegroundColor Green
Write-Host ""

# 4. Restart aplikacji
Write-Host "4. Sprawdzanie metody uruchomienia aplikacji..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Wykrywanie metody uruchomienia:" -ForegroundColor Cyan

# SprawdĹş docker-compose
ssh "$DEV_USER@$DEV_HOST" "cd $DEV_PATH && docker-compose ps 2>/dev/null | grep -q 'Up'" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "âś“ Wykryto Docker Compose" -ForegroundColor Green
    Write-Host "RestartujÄ™ backend przez docker-compose..." -ForegroundColor Yellow
    ssh "$DEV_USER@$DEV_HOST" "cd $DEV_PATH && docker-compose restart backend"
    Write-Host "âś“ Backend zrestartowany" -ForegroundColor Green
} else {
    # SprawdĹş systemd
    ssh "$DEV_USER@$DEV_HOST" "systemctl is-active --quiet digital-signage-backend 2>/dev/null"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "âś“ Wykryto systemd service" -ForegroundColor Green
        Write-Host "RestartujÄ™ backend przez systemctl..." -ForegroundColor Yellow
        ssh "$DEV_USER@$DEV_HOST" "sudo systemctl restart digital-signage-backend"
        Write-Host "âś“ Backend zrestartowany" -ForegroundColor Green
    } else {
        # SprawdĹş proces uvicorn
        ssh "$DEV_USER@$DEV_HOST" "pgrep -f 'uvicorn.*app.main:app' >/dev/null 2>&1"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "âś“ Wykryto proces uvicorn" -ForegroundColor Green
            Write-Host "UWAGA: Musisz rÄ™cznie zrestartowaÄ‡ backend!" -ForegroundColor Yellow
            Write-Host "Wykonaj na dev1:" -ForegroundColor Cyan
            Write-Host "  pkill -f uvicorn" -ForegroundColor White
            Write-Host "  cd $DEV_PATH/backend && uvicorn app.main:app --reload &" -ForegroundColor White
        } else {
            Write-Host "âš  Nie wykryto metody uruchomienia" -ForegroundColor Yellow
            Write-Host "Musisz rÄ™cznie zrestartowaÄ‡ backend na dev1" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "=== Deploy zakoĹ„czony ===" -ForegroundColor Cyan
Write-Host "SprawdĹş aplikacjÄ™: http://$DEV_HOST:8000/docs" -ForegroundColor Green


