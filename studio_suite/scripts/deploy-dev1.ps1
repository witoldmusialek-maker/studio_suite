param(
  [string]$DevHost = "192.168.50.20",
  [string]$RemoteRepoRoot = "~/projects/projekt2_repo",
  [string]$Branch = "feature/legacy-caisse-flow"
)

$ErrorActionPreference = "Stop"

function Run-Native([string]$Cmd) {
  cmd /c $Cmd
  if ($LASTEXITCODE -ne 0) { throw "Command failed ($LASTEXITCODE): $Cmd" }
}

Write-Host "[1/3] Pull + deploy na current operational host ($DevHost, $Branch)..."
Run-Native "ssh $DevHost `"cd $RemoteRepoRoot && git fetch origin && git checkout $Branch && git pull origin $Branch && cd studio_suite && docker compose up -d --build && docker compose ps`""

Write-Host "[2/3] Smoke test health..."
& "$PSScriptRoot\smoke-test.ps1" -BaseUrl "http://192.168.50.20:8003" -HealthOnly

Write-Host "[3/3] DONE: deploy + smoke zakończone."


