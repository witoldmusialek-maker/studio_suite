param(
  [string]$DevHost = "witold@192.168.200.116",
  [string]$RemoteRepo = "~/projects/digital_signage_repo/digital_signage",
  [string]$DbUser = "ds_user",
  [string]$DbName = "digital_signage"
)

$ErrorActionPreference = "Stop"

function Run-Native([string]$Cmd) {
  cmd /c $Cmd
  if ($LASTEXITCODE -ne 0) {
    throw "Command failed ($LASTEXITCODE): $Cmd"
  }
}

Set-Location (Join-Path $PSScriptRoot "..")
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$tmpDir = Join-Path $PWD ".tmp_sync"
$dbDump = Join-Path $tmpDir "db_$timestamp.sql"
$contentTar = Join-Path $tmpDir "content_$timestamp.tar"

New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null

Write-Host "[1/6] Dump lokalnej bazy (UTF-8 bytes)..."
Run-Native "docker compose exec -T db pg_dump -U $DbUser -d $DbName --clean --if-exists > `"$dbDump`""

Write-Host "[2/6] Upload dumpa na dev..."
Run-Native "scp `"$dbDump`" $DevHost`:~/db_sync.sql"

Write-Host "[3/6] Restore bazy na dev..."
Run-Native "ssh $DevHost `"cd $RemoteRepo && docker compose exec -T db psql -U $DbUser -d $DbName < ~/db_sync.sql`""

Write-Host "[4/6] Pakowanie backend/content..."
if (Test-Path ".\backend\content") {
  Run-Native "tar -cf `"$contentTar`" -C .\backend content"

  Write-Host "[5/6] Upload content i rozpakowanie na dev (sudo)..."
  Run-Native "scp `"$contentTar`" $DevHost`:~/content_sync.tar"
  Run-Native "ssh $DevHost `" mkdir -p $RemoteRepo/backend/content && tar -xf ~/content_sync.tar -C $RemoteRepo/backend && rm -f ~/content_sync.tar`""
} else {
  Write-Host "Brak .\backend\content - pomijam."
}

Write-Host "[6/6] Sprz�tanie..."
Remove-Item -Force $dbDump -ErrorAction SilentlyContinue
Remove-Item -Force $contentTar -ErrorAction SilentlyContinue
Run-Native "ssh $DevHost `"rm -f ~/db_sync.sql`""

Write-Host "DONE: sync lokalny -> dev zako�czony."
