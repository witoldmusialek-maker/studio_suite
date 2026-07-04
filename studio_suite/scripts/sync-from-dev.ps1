param(
  [string]$DevHost = "192.168.50.20",
  [string]$RemoteRepo = "~/projects/projekt2_repo/studio_suite",
  [string]$DbUser = "ds_user",
  [string]$DbName = "studio_suite"
)

$ErrorActionPreference = "Stop"

function Run-Native([string]$Cmd) {
  cmd /c $Cmd
  if ($LASTEXITCODE -ne 0) { throw "Command failed ($LASTEXITCODE): $Cmd" }
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$tmpDir = Join-Path $PWD ".tmp_sync"
$dbDump = Join-Path $tmpDir "db_from_dev_$timestamp.sql"
$contentTar = Join-Path $tmpDir "content_from_dev_$timestamp.tar"

New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null

Write-Host "[1/6] Dump DB na dev..."
Run-Native "ssh $DevHost `"cd $RemoteRepo && docker compose exec -T db pg_dump -U $DbUser -d $DbName --clean --if-exists > ~/db_from_dev.sql`""

Write-Host "[2/6] Pobranie dumpa..."
Run-Native "scp $DevHost`:~/db_from_dev.sql `"$dbDump`""

Write-Host "[3/6] Restore DB lokalnie..."
Run-Native "docker compose exec -T db psql -U $DbUser -d $DbName < `"$dbDump`""

Write-Host "[4/6] Pakowanie content na dev..."
Run-Native "ssh $DevHost `"cd $RemoteRepo/backend && tar -cf ~/content_from_dev.tar content`""

Write-Host "[5/6] Pobranie i rozpakowanie content lokalnie..."
Run-Native "scp $DevHost`:~/content_from_dev.tar `"$contentTar`""
if (Test-Path ".\backend\content") { Remove-Item -Recurse -Force ".\backend\content" }
Run-Native "tar -xf `"$contentTar`" -C .\backend"

Write-Host "[6/6] Sprzątanie..."
Run-Native "ssh $DevHost `"rm -f ~/db_from_dev.sql ~/content_from_dev.tar`""
Remove-Item -Force $dbDump,$contentTar -ErrorAction SilentlyContinue

Write-Host "DONE: sync dev -> lokalny zakończony."


